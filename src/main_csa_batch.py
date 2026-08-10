"""Batch runner for the GJB8114 CSA checker factory."""

import argparse
import datetime
import fcntl
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from csa_generator import CSACheckerGenerator
from main_csa import DEFAULT_LLM_CONFIG, DEFAULT_RULE_FILE, REPO_ROOT, load_cases, load_rule
from plateform.csa import validate_csa_environment
from retriever.csa_embedding import DEFAULT_MODEL


# no-assignment-in-condition and no-else-branch are measured like every other
# rule now. The former is kept honest with --no-deterministic-fallback.
DEFAULT_EXCLUDES = set()


def _rule_records(rule_file):
    data = json.loads(Path(rule_file).read_text(encoding="utf-8"))
    return [record for group in data.get("data", {}).values() for record in group]


def _parse_precomputed(values):
    result = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError("--precomputed-result must use RULE=JSON_PATH")
        rule, path = value.split("=", 1)
        result[rule] = Path(path).resolve()
    return result


def build_parser():
    parser = argparse.ArgumentParser(description="Run GJB8114 CSA checker generation for multiple rules")
    parser.add_argument("--rule-file", type=Path, default=DEFAULT_RULE_FILE)
    parser.add_argument("--result-dir", type=Path, default=REPO_ROOT / "result-generation-all-rules")
    parser.add_argument("--llvm-root", type=Path, default=Path("/home/llvm/llvm-project"))
    parser.add_argument("--llvm-build", type=Path, default=Path("/home/checker/llvm-build"))
    parser.add_argument("--exclude-rule", action="append", default=[])
    parser.add_argument("--precomputed-result", action="append", default=[],
                        help="Reuse RULE=checker_generation_result.json instead of rerunning it")
    parser.add_argument("--resume", action="store_true",
                        help="Reuse completed per-rule results already present in result-dir")
    parser.add_argument("--fresh", action="store_true",
                        help="Delete each rule's previous output before rerunning it")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--llm-config", type=Path, default=DEFAULT_LLM_CONFIG)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--retrieval", choices=("embedding", "lexical"), default="embedding")
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument("--embedding-cache", type=Path, default=REPO_ROOT / "src/embedding_db/csa")
    parser.add_argument("--max-initial-negative-cases", type=int, default=3)
    parser.add_argument("--max-round", type=int, default=3)
    parser.add_argument("--max-compiler-trys", type=int, default=4)
    parser.add_argument("--max-augmentation-tries", type=int, default=16)
    parser.add_argument("--max-semantic-repair-tries", type=int, default=3)
    parser.add_argument("--max-technical-retries-per-case", type=int, default=2)
    parser.add_argument("--max-execution-repair-tries", type=int, default=2)
    parser.add_argument("--max-rule-seconds", type=int, default=2400)
    parser.add_argument("--jobs", type=int, default=6,
                        help="Parallel clang --analyze invocations per regression run")
    parser.add_argument("--no-deterministic-fallback", action="store_true",
                        help="Disable the hardcoded offline checker for no-assignment-in-condition")
    parser.add_argument("--no-promote-with-execution-failures", action="store_true",
                        help="Never ship a higher-scoring checker that crashes the analyzer")
    return parser


def _git_revision():
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _write_run_manifest(result_dir, args, llm):
    """Without this, a score change cannot be attributed to a change you made."""
    manifest = {
        "git_revision": _git_revision(),
        "argv": sys.argv,
        "hostname": socket.gethostname(),
        "started_at": datetime.datetime.now().astimezone().isoformat(),
        "llm_model": getattr(llm, "model", None),
        "parameters": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in sorted(vars(args).items())
            if key not in {"llm_config"}
        },
    }
    (result_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def _failure_result(rule_name, error, result_path):
    value = {
        "stage": "CSA_BATCH",
        "rule": rule_name,
        "run_status": "execution_failure",
        "termination_reason": "batch_rule_exception",
        "failure_reason": str(error),
        "success_case_list": [],
        "failed_case_list": [],
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    return value


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.fresh and args.resume:
        parser.error("--fresh and --resume are mutually exclusive")
    environment = validate_csa_environment(args.llvm_root, args.llvm_build)
    if not environment["success"]:
        raise SystemExit("CSA build environment is incomplete: " + ", ".join(environment["missing"]))

    excludes = DEFAULT_EXCLUDES | set(args.exclude_rule)
    precomputed = _parse_precomputed(args.precomputed_result)
    args.result_dir.mkdir(parents=True, exist_ok=True)
    # Two concurrent batches once interleaved into one tree and left stale JSON
    # that contradicted its own manifests. Fail loudly instead.
    lock_handle = open(args.result_dir / ".lock", "w")
    try:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit(f"another batch is already writing to {args.result_dir}")
    lock_handle.write(f"{os.getpid()}\n")
    lock_handle.flush()
    llm = None
    if args.use_llm:
        from llm_interface.csa_llm_provider import load_csa_chat_client
        llm = load_csa_chat_client(args.llm_config, args.llm_model)
    _write_run_manifest(args.result_dir, args, llm)

    records = _rule_records(args.rule_file)
    summary = {
        "stage": "CSA_BATCH",
        "excluded_rules": sorted(excludes),
        "executed_rule_amount": 0,
        "success_rule_list": [],
        "failed_rule_list": [],
        "execution_failure_rule_list": [],
        "rule_result_path_map": {},
        "rule_status_list": [],
        "total_token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "total_cost": None,
        "termination_reason": "completed",
    }
    summary_path = args.result_dir / "csa_batch_result.json"

    def checkpoint():
        summary["all_rules_success"] = not summary["failed_rule_list"] and not summary["execution_failure_rule_list"]
        summary["result_dir"] = str(args.result_dir.resolve())
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    for record in records:
        rule_name = record.get("main_title")
        if not rule_name or rule_name in excludes:
            continue
        summary["executed_rule_amount"] += 1
        started = time.monotonic()
        result_path = args.result_dir / "csa" / rule_name / "checker_generation_result.json"
        if args.resume and result_path.exists() and rule_name not in precomputed:
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                status = result.get("run_status")
                if status in {"success", "partial", "failed", "execution_failure"}:
                    summary["rule_result_path_map"][rule_name] = str(result_path.resolve())
                    summary["rule_status_list"].append({"rule": rule_name, "status": "resumed",
                                                         "source_status": status, "elapsed_seconds": 0})
                    if status == "success" or result.get("all_cases_success"):
                        summary["success_rule_list"].append(rule_name)
                    elif status == "execution_failure":
                        summary["execution_failure_rule_list"].append(rule_name)
                    else:
                        summary["failed_rule_list"].append(rule_name)
                    for key in summary["total_token_usage"]:
                        summary["total_token_usage"][key] += result.get("token_usage", {}).get(key, 0) or 0
                    checkpoint()
                    continue
            except (OSError, json.JSONDecodeError):
                pass
        if rule_name in precomputed:
            try:
                result = json.loads(precomputed[rule_name].read_text(encoding="utf-8"))
                status = result.get("run_status", "success" if result.get("all_cases_success") else "failed")
                summary["rule_result_path_map"][rule_name] = str(precomputed[rule_name])
                summary["rule_status_list"].append({"rule": rule_name, "status": "precomputed",
                                                     "source_status": status, "elapsed_seconds": 0})
                if status == "success" or result.get("all_cases_success"):
                    summary["success_rule_list"].append(rule_name)
                else:
                    summary["failed_rule_list"].append(rule_name)
                checkpoint()
            except Exception as exc:
                failure = _failure_result(rule_name, exc, result_path)
                summary["execution_failure_rule_list"].append(rule_name)
                summary["rule_status_list"].append({"rule": rule_name, "status": failure["run_status"],
                                                     "elapsed_seconds": time.monotonic() - started})
                checkpoint()
            continue
        try:
            test_dir = REPO_ROOT / "experiment/gjb8114/codeql_test_case" / rule_name.replace("-", "_")
            if args.fresh:
                shutil.rmtree(args.result_dir / "csa" / rule_name, ignore_errors=True)
            cases = load_cases(test_dir)
            rule = load_rule(args.rule_file, rule_name, test_dir, cases)
            generator = CSACheckerGenerator(
                rule, cases, rule_result_dir=args.result_dir,
                max_initial_negative_cases=args.max_initial_negative_cases,
                max_round=args.max_round, max_compiler_trys=args.max_compiler_trys,
                max_augmentation_tries=args.max_augmentation_tries,
                max_semantic_repair_tries=args.max_semantic_repair_tries,
                max_technical_retries_per_case=args.max_technical_retries_per_case,
                max_execution_repair_tries=args.max_execution_repair_tries,
                max_rule_seconds=args.max_rule_seconds,
                jobs=args.jobs,
                use_deterministic_fallback=not args.no_deterministic_fallback,
                promote_with_execution_failures=not args.no_promote_with_execution_failures,
                llvm_root=args.llvm_root, llvm_build=args.llvm_build, llm=llm,
                retrieval_mode=args.retrieval, embedding_model=args.embedding_model,
                embedding_cache=args.embedding_cache)
            generator.generate_checker()
            result = json.loads(result_path.read_text(encoding="utf-8"))
            summary["rule_result_path_map"][rule_name] = str(result_path.resolve())
            status = result.get("run_status", "success" if result.get("all_cases_success") else "failed")
            summary["rule_status_list"].append({"rule": rule_name, "status": status,
                                                 "elapsed_seconds": time.monotonic() - started})
            if status == "success" or result.get("all_cases_success"):
                summary["success_rule_list"].append(rule_name)
            elif status == "execution_failure":
                summary["execution_failure_rule_list"].append(rule_name)
            else:
                summary["failed_rule_list"].append(rule_name)
            for key in summary["total_token_usage"]:
                summary["total_token_usage"][key] += result.get("token_usage", {}).get(key, 0) or 0
            checkpoint()
        except Exception as exc:
            failure = _failure_result(rule_name, exc, result_path)
            summary["execution_failure_rule_list"].append(rule_name)
            summary["rule_result_path_map"][rule_name] = str(result_path.resolve())
            summary["rule_status_list"].append({"rule": rule_name, "status": failure["run_status"],
                                                 "elapsed_seconds": time.monotonic() - started})
            checkpoint()

    checkpoint()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
