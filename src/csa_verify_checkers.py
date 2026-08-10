"""Independently re-verify delivered CSA checkers against their full case suite.

Reads nothing from the generation result except which artifact was shipped,
then reloads that plugin and reruns every case through the same
CSACheckerGenerator classification path used during generation.
"""

import argparse
import json
import shutil
from pathlib import Path

from csa_generator import CSACheckerGenerator
from entity.concreteProduct_CSA import Checker_CSA
from main_csa import DEFAULT_RULE_FILE, REPO_ROOT, load_cases, load_rule


def verify(rule_name, result_path, jobs=6):
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    source = data.get("final_checker_source")
    plugin = data.get("final_plugin_path")
    if not plugin or not Path(plugin).exists():
        return {"rule": rule_name, "error": f"missing plugin: {plugin}"}
    test_dir = REPO_ROOT / "experiment/gjb8114/codeql_test_case" / rule_name.replace("-", "_")
    cases = load_cases(test_dir)
    rule = load_rule(DEFAULT_RULE_FILE, rule_name, test_dir, cases)
    generator = CSACheckerGenerator(rule, cases, retrieval_mode="lexical", jobs=jobs)
    checker = Checker_CSA(
        checker_code=Path(source).read_text(encoding="utf-8") if source and Path(source).exists() else "",
        name=generator.checker_name, frontend=generator.frontend,
        plugin_path=str(Path(plugin).resolve()), version=0)
    results = generator.run_all_test_cases(checker, write_result=False)
    passed = sum(bool(item["success"]) for item in results)
    return {
        "rule": rule_name,
        "checker": generator.checker_name,
        "frontend": generator.frontend,
        "rule_id": rule.get_rule_id(),
        "diagnostic": rule.get_diagnostic(),
        "passed": passed,
        "total": len(results),
        "negatives": sum(1 for item in results if item["case_type"] == "negative"),
        "positives": sum(1 for item in results if item["case_type"] == "positive"),
        "failures": [
            {"case": Path(item["case_path"]).name, "category": item["failure_category"]}
            for item in results if not item["success"]
        ],
        "source": source,
        "plugin": plugin,
    }


def collect(report, out_dir):
    """Copy the verified checkers into one delivery tree."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in report:
        if item.get("error"):
            continue
        target = out_dir / item["rule"]
        target.mkdir(parents=True, exist_ok=True)
        if item["source"] and Path(item["source"]).exists():
            shutil.copy2(item["source"], target / f"{item['checker']}.cpp")
        if Path(item["plugin"]).exists():
            shutil.copy2(item["plugin"], target / f"{item['checker']}.so")
        (target / "verification.json").write_text(
            json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")


def build_parser():
    parser = argparse.ArgumentParser(description="Re-verify and collect delivered CSA checkers")
    parser.add_argument("--source", action="append", required=True,
                        help="RULE=checker_generation_result.json, repeatable")
    parser.add_argument("--collect-into", type=Path, default=None)
    parser.add_argument("--jobs", type=int, default=6)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    pairs = []
    for value in args.source:
        rule, _, path = value.partition("=")
        pairs.append((rule, path))
    report = [verify(rule, path, args.jobs) for rule, path in sorted(pairs)]
    width = max(len(item["rule"]) for item in report) + 2
    total = passed_total = 0
    print(f"{'rule':<{width}}{'verified':>10}  {'frontend':<44}status")
    print("-" * (width + 66))
    for item in report:
        if item.get("error"):
            print(f"{item['rule']:<{width}}{'ERROR':>10}  {item['error']}")
            continue
        total += item["total"]
        passed_total += item["passed"]
        status = "OK" if item["passed"] == item["total"] else \
            "FAIL: " + ", ".join(f"{f['case']}({f['category']})" for f in item["failures"][:3])
        print(f"{item['rule']:<{width}}{item['passed']:>6}/{item['total']:<3}  {item['frontend']:<44}{status}")
    print("-" * (width + 66))
    print(f"{'TOTAL':<{width}}{passed_total:>6}/{total:<3}")
    if args.collect_into:
        collect(report, args.collect_into)
        print(f"\ncollected into {args.collect_into}")
    return 0 if passed_total == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
