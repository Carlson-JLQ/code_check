"""Summarise CSA batch results, and diff two runs.

Every comparison used to be hand-written `python3 -c` archaeology over the
result tree, which is how stale artifacts from an earlier run went unnoticed.
"""

import argparse
import json
from pathlib import Path


FIELDS = ("performance", "run_status", "termination_reason")


def load_run(result_dir):
    root = Path(result_dir) / "csa"
    rules = {}
    for path in sorted(root.glob("*/checker_generation_result.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            rules[path.parent.name] = {"rule": path.parent.name, "error": str(exc)}
            continue
        passed, total = _score(data)
        rules[data.get("rule", path.parent.name)] = {
            "rule": data.get("rule", path.parent.name),
            "passed": passed,
            "total": total,
            "performance": data.get("performance"),
            "run_status": data.get("run_status"),
            "termination_reason": data.get("termination_reason"),
            "best_score": data.get("best_score"),
            "promoted_from_best": data.get("promoted_from_best"),
            "crashes": data.get("final_execution_failure_amount"),
            "accepted": data.get("accepted_augmentation_amount"),
            "rejected": data.get("rejected_augmentation_amount"),
            "attempts": data.get("augmentation_attempts"),
            "logic_parse_failures": data.get("logic_parse_failure_amount"),
            "initial_compile_success": data.get("initial_compile_success"),
            "tokens": (data.get("token_usage") or {}).get("total_tokens", 0) or 0,
            "model": data.get("llm_model"),
            "path": str(path),
        }
    return rules


def _score(data):
    """Score against the real case suite, not the candidate count.

    A rule whose initial generation failed writes `performance` as
    passed/candidates-tried ("0/6"), so reading that field would silently
    shrink the denominator for exactly the worst rules.
    """
    total = (data.get("negative_case_amount") or 0) + (data.get("positive_case_amount") or 0)
    successes = data.get("success_case_list") or []
    failures = data.get("failed_case_list") or []
    passed = len({item.get("case_path") for item in successes if item.get("case_path")})
    if not total:
        total = passed + len({item.get("case_path") for item in failures if item.get("case_path")})
    return passed, total


def _elapsed(result_dir):
    summary = Path(result_dir) / "csa_batch_result.json"
    if not summary.exists():
        return {}
    try:
        data = json.loads(summary.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {item.get("rule"): item.get("elapsed_seconds")
            for item in data.get("rule_status_list", [])}


def report(result_dir, baseline_dir=None):
    rules = load_run(result_dir)
    elapsed = _elapsed(result_dir)
    baseline = load_run(baseline_dir) if baseline_dir else {}
    header = f"{'rule':<42}{'score':>8}{'delta':>8}  {'status':<10}{'best':>5}{'crash':>6}{'a/r':>7}{'lpf':>5}{'secs':>7}"
    print(header)
    print("-" * len(header))
    total_passed = total_cases = total_tokens = 0
    for name in sorted(rules):
        item = rules[name]
        if "error" in item:
            print(f"{name:<42}  UNREADABLE: {item['error']}")
            continue
        total_passed += item["passed"]
        total_cases += item["total"]
        total_tokens += item["tokens"]
        delta = ""
        if baseline.get(name) and "passed" in baseline[name]:
            difference = item["passed"] - baseline[name]["passed"]
            delta = f"{difference:+d}" if difference else "0"
        seconds = elapsed.get(name)
        print(
            f"{name:<42}"
            f"{item['passed']:>4}/{item['total']:<3}"
            f"{delta:>8}  "
            f"{(item['run_status'] or '-'):<10}"
            f"{(item['best_score'] if item['best_score'] is not None else '-'):>5}"
            f"{(item['crashes'] if item['crashes'] is not None else '-'):>6}"
            f"{str(item['accepted']) + '/' + str(item['rejected']):>7}"
            f"{(item['logic_parse_failures'] if item['logic_parse_failures'] is not None else '-'):>5}"
            f"{(f'{seconds:.0f}' if isinstance(seconds, (int, float)) else '-'):>7}"
        )
    print("-" * len(header))
    rate = (100.0 * total_passed / total_cases) if total_cases else 0.0
    print(f"{'TOTAL':<42}{total_passed:>4}/{total_cases:<3}{'':>8}  {rate:.1f}%   tokens={total_tokens:,}")
    if baseline:
        base_passed = sum(item.get("passed", 0) for item in baseline.values())
        base_cases = sum(item.get("total", 0) for item in baseline.values())
        print(f"{'BASELINE':<42}{base_passed:>4}/{base_cases:<3}"
              f"{'':>8}  {(100.0 * base_passed / base_cases if base_cases else 0):.1f}%")
    promoted = [name for name, item in rules.items() if item.get("promoted_from_best")]
    if promoted:
        print("\npromoted from best candidate: " + ", ".join(sorted(promoted)))
    missing = sorted(set(baseline) - set(rules))
    if missing:
        print("not present in this run: " + ", ".join(missing))
    return rules


def build_parser():
    parser = argparse.ArgumentParser(description="Summarise a CSA batch result directory")
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--against", type=Path, default=None,
                        help="Baseline result directory to diff per-rule scores against")
    parser.add_argument("--json", action="store_true", help="Emit the raw per-rule records")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    rules = report(args.result_dir, args.against)
    if args.json:
        print(json.dumps(rules, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
