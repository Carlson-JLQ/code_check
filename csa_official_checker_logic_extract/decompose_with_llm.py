#!/usr/bin/env python3
"""Ask an OpenAI-compatible LLM to split CSA checker callback slices."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from .static_analysis import StaticAnalyzer
except ImportError:  # Direct script execution.
    from static_analysis import StaticAnalyzer


def parse_json_response(content: str) -> dict[str, Any]:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content, flags=re.I | re.S)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("LLM response must be a JSON object")
    return value


class CompatibleChatClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 180):
        normalized = base_url.rstrip("/")
        # Accept either an OpenAI base URL (already ending in /v1) or a host.
        if not re.search(r"/v\d+(?:/|$)", normalized):
            normalized += "/v1"
        self.url = normalized + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "temperature": 0,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise urllib.error.URLError(f"HTTP {exc.code}: {detail}") from exc
        return body["choices"][0]["message"]["content"]


def numbered_source(lines: list[str], start: int, end: int) -> str:
    return "\n".join(f"{line_no:5d}: {lines[line_no - 1]}" for line_no in range(start, end + 1))


def checker_prompt(
    prompt_template: str,
    inventory: dict[str, Any],
    checker: dict[str, Any],
    llvm_root: Path,
) -> str:
    functions = {item["symbol"]: item for item in inventory["functions"]}
    slices = [
        item for item in inventory["callback_slices"]
        if item["callback"]["method"].startswith(checker["implementation_class"] + "::")
    ]
    symbols = []
    for item in slices:
        for symbol in item["symbols_in_call_order"]:
            if symbol not in symbols:
                symbols.append(symbol)
    lines = (llvm_root / inventory["file"]).read_text(encoding="utf-8").splitlines()
    source_sections = []
    for symbol in symbols:
        function = functions[symbol]
        source_sections.append(
            f"## {symbol}\n" + numbered_source(lines, function["start_line"], function["end_line"])
        )
    registrations = [
        item for item in inventory["registrations"]
        if item["implementation_class"] in {None, checker["implementation_class"]}
    ]
    context = {
        "implementation_class": checker["implementation_class"],
        "source_file": inventory["file"],
        "callbacks": checker["callbacks"],
        "callback_slices": slices,
        "frontends": registrations,
        "state_traits": inventory["state_traits"],
        "direct_checker_headers": inventory["direct_checker_headers"],
    }
    return (
        prompt_template
        + "\n\n# Static context\n\n```json\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n```\n\n# Exact numbered source\n\n"
        + "\n\n".join(source_sections)
        + "\n\nReturn an object with `summary`, `analysis_mode`, and `logic_units`. "
        "Each source selector must use the supplied file, symbol, role, start_line, and end_line. "
        "Use frontend names (not IDs) in `applies_to_frontends`. Include `api_names` as Stage 1 "
        "qualified API names only when the selected source visibly calls that API."
    )


def validate_llm_plan(plan: dict[str, Any], checker: dict[str, Any], inventory: dict[str, Any]) -> None:
    required = {"summary", "analysis_mode", "logic_units"}
    missing = required - set(plan)
    if missing:
        raise ValueError(f"LLM plan lacks fields: {sorted(missing)}")
    raw_mode = str(plan["analysis_mode"])
    compact_mode = re.sub(r"[^a-z]", "", raw_mode.lower())
    mode_aliases = {
        "pathsensitive": "path_sensitive",
        "pathinsensitive": "path_insensitive",
        "hybrid": "hybrid",
    }
    plan["analysis_mode"] = mode_aliases.get(compact_mode, raw_mode)
    if plan["analysis_mode"] not in {"path_sensitive", "path_insensitive", "hybrid"}:
        raise ValueError(f"invalid analysis_mode: {raw_mode!r}")
    allowed_symbols = {item["symbol"]: item for item in inventory["functions"]}
    slugs = set()
    for unit in plan["logic_units"]:
        unit_required = {
            "slug", "kind", "meta_op", "callback_context", "applies_to_frontends",
            "depends_on", "behavior", "source_selectors", "api_names",
        }
        if unit_required - set(unit):
            raise ValueError(f"unit lacks fields: {sorted(unit_required - set(unit))}")
        if unit["slug"] in slugs:
            raise ValueError(f"duplicate unit slug: {unit['slug']}")
        slugs.add(unit["slug"])
        for selector in unit["source_selectors"]:
            symbol = selector.get("symbol")
            function = allowed_symbols.get(symbol)
            if function is None:
                raise ValueError(f"unknown source selector symbol: {symbol}")
            if not (function["start_line"] <= selector.get("start_line", 0) <= selector.get("end_line", 0) <= function["end_line"]):
                raise ValueError(f"selector escapes function boundary: {selector}")
    for unit in plan["logic_units"]:
        unknown = set(unit["depends_on"]) - slugs
        if unknown:
            raise ValueError(f"unknown dependency slugs: {sorted(unknown)}")


def run_decomposition(
    analyzer: StaticAnalyzer,
    source_files: list[Path],
    prompt_template: str,
    complete: Callable[[str], str],
    retries: int,
    checker_names: set[str] | None = None,
) -> dict[str, Any]:
    results = []
    for path in source_files:
        inventory = analyzer.analyze_file(path)
        inventory["callback_slices"] = analyzer.callback_slices(inventory)
        for checker in inventory["checker_classes"]:
            if checker_names and checker["implementation_class"] not in checker_names:
                continue
            prompt = checker_prompt(prompt_template, inventory, checker, analyzer.llvm_root)
            last_error: Exception | None = None
            for attempt in range(1, retries + 1):
                try:
                    plan = parse_json_response(complete(prompt))
                    validate_llm_plan(plan, checker, inventory)
                    results.append({
                        "implementation_class": checker["implementation_class"],
                        "source_files": [inventory["file"], *inventory["direct_checker_headers"]],
                        "callbacks": checker["callbacks"],
                        "frontends": inventory["registrations"],
                        "state_traits": inventory["state_traits"],
                        **plan,
                    })
                    break
                except (ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError) as exc:
                    last_error = exc
                    if attempt < retries:
                        time.sleep(min(2 ** (attempt - 1), 8))
            else:
                raise RuntimeError(f"failed to decompose {checker['implementation_class']}: {last_error}")
    return {"schema_version": "llm-semantic-plan-1.0", "checkers": results}


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-root", type=Path, default=Path("/home/llvm/llvm-project"))
    parser.add_argument("--checker", action="append", dest="checkers", required=True, help="Implementation class to decompose (repeatable)")
    parser.add_argument(
        "--config",
        type=Path,
        default=here.parent / "csa_official_api_extract/llm_config_csa_meta_op.json",
        help="JSON config containing base_url and key",
    )
    parser.add_argument("--model", help="Override config model")
    parser.add_argument("--base-url", help="Override config base_url")
    parser.add_argument("--api-key-env", default="CSA_LLM_API_KEY")
    parser.add_argument("--api-key", help="Override config key; prefer the config file or environment")
    parser.add_argument("--prompt", type=Path, default=here / "prompts/semantic_decomposition.md")
    parser.add_argument("--output", type=Path, default=here / "semantic_plan.json")
    parser.add_argument("--retries", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config.is_file() else {}
    api_key = args.api_key or os.getenv(args.api_key_env) or config.get("key") or config.get("api_key")
    if not api_key:
        raise SystemExit(f"Missing API key in environment variable {args.api_key_env}")
    base_url = args.base_url or os.getenv("CSA_LLM_BASE_URL") or config.get("base_url")
    if not base_url:
        raise SystemExit("Missing base_url in --config or CSA_LLM_BASE_URL")
    model = args.model or os.getenv("CSA_LLM_MODEL") or config.get("model") or "deepseek-chat"
    analyzer = StaticAnalyzer(args.llvm_root)
    inventories = []
    wanted = set(args.checkers)
    for path in sorted(analyzer.checker_root.glob("*.cpp")):
        inventory = analyzer.analyze_file(path)
        classes = {item["implementation_class"] for item in inventory["checker_classes"]}
        if classes.intersection(wanted):
            inventories.append(path)
            wanted -= classes
    if wanted:
        raise SystemExit(f"Checker implementation classes not found: {', '.join(sorted(wanted))}")
    client = CompatibleChatClient(base_url, api_key, model)
    result = run_decomposition(
        analyzer,
        inventories,
        args.prompt.read_text(encoding="utf-8"),
        client.complete,
        args.retries,
        set(args.checkers),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved LLM semantic plans for {len(result['checkers'])} checkers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
