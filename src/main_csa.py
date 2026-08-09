"""CLI for the GJB8114 Clang Static Analyzer generation lifecycle."""

import argparse
import json
import re
from pathlib import Path

from csa_generator import CSACheckerGenerator, expected_diagnostics
from entity.concreteProduct_CSA import Case_CSA, Rule_CSA
from plateform.csa import validate_csa_environment
from retriever.csa_embedding import DEFAULT_MODEL


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DIR = REPO_ROOT / "experiment/gjb8114/codeql_test_case/no_assignment_in_condition"
DEFAULT_RULE_FILE = REPO_ROOT / "experiment/gjb8114/rule_codeql/jgb8114_all_rules.json"
DEFAULT_LLM_CONFIG = REPO_ROOT / "csa_official_api_extract/llm_config_csa_meta_op.json"
RULE_ID_RE = re.compile(r"\[(gjb8114-r-[^]]+)\]", re.I)


def load_cases(test_dir):
    paths = sorted(
        (path for path in Path(test_dir).rglob("*") if path.suffix in {".c", ".cc", ".cpp", ".cxx"}),
        key=lambda path: path.name,
    )
    cases = []
    for path in paths:
        code = path.read_text(encoding="utf-8")
        expected = expected_diagnostics(code)
        cases.append(Case_CSA(
            case_code=code,
            case_path=str(path.resolve()),
            case_flag=not bool(expected),
            expected_diagnostics=expected,
        ))
    return cases


def load_rule(rule_file=DEFAULT_RULE_FILE, rule_name="no-assignment-in-condition",
              test_dir=DEFAULT_TEST_DIR, cases=None):
    data = json.loads(Path(rule_file).read_text(encoding="utf-8"))
    records = [record for group in data.get("data", {}).values() for record in group]
    record = next((record for record in records if record.get("main_title") == rule_name), None)
    if record is None:
        raise ValueError(f"rule {rule_name!r} not found in {rule_file}")
    cases = list(cases or load_cases(test_dir))
    negative = next((case for case in cases if case.expected_diagnostics), None)
    if negative is None:
        raise ValueError(f"rule {rule_name!r} has no negative test case")
    match = RULE_ID_RE.search(negative.get_case_code())
    if match is None:
        raise ValueError(f"rule id is missing from negative tests for {rule_name!r}")
    return Rule_CSA.from_rule_record(
        record,
        test_path=Path(test_dir).resolve(),
        rule_id=match.group(1).lower(),
        diagnostic=negative.expected_diagnostics[0],
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Generate and validate a GJB8114 CSA checker")
    parser.add_argument("test_dir", nargs="?", type=Path, default=None)
    parser.add_argument("--rule-file", type=Path, default=DEFAULT_RULE_FILE)
    parser.add_argument("--rule-name", default="no-assignment-in-condition")
    parser.add_argument("--result-dir", type=Path, default=REPO_ROOT / "result-generation")
    parser.add_argument("--llvm-root", type=Path, default=Path("/home/llvm/llvm-project"))
    parser.add_argument("--llvm-build", type=Path, default=Path("/home/checker/llvm-build"))
    parser.add_argument("--max-round", type=int, default=2)
    parser.add_argument("--max-compiler-trys", type=int, default=2)
    parser.add_argument("--max-augmentation-tries", type=int, default=4)
    parser.add_argument("--first-checker-only", action="store_true")
    parser.add_argument("--check-environment", action="store_true")
    parser.add_argument("--use-llm", action="store_true",
                        help="Use the project's configured LLM instead of only the offline baseline")
    parser.add_argument("--llm-config", type=Path, default=DEFAULT_LLM_CONFIG)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--list-llm-models", action="store_true")
    parser.add_argument("--retrieval", choices=("embedding", "lexical"), default="embedding")
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument("--embedding-cache", type=Path,
                        default=REPO_ROOT / "src/embedding_db/csa")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    test_dir = args.test_dir or (
        REPO_ROOT / "experiment/gjb8114/codeql_test_case" / args.rule_name.replace("-", "_")
    )
    environment = validate_csa_environment(args.llvm_root, args.llvm_build)
    if args.check_environment:
        print(json.dumps(environment, indent=2, ensure_ascii=False))
        return 0 if environment["success"] else 1
    if not environment["success"]:
        raise SystemExit("CSA build environment is incomplete: " + ", ".join(environment["missing"]))
    cases = load_cases(test_dir)
    rule = load_rule(args.rule_file, args.rule_name, test_dir, cases)
    llm = None
    if args.use_llm:
        from llm_interface.csa_llm_provider import load_csa_chat_client

        llm = load_csa_chat_client(args.llm_config, args.llm_model)
        if args.list_llm_models:
            print(json.dumps(llm.list_models(), indent=2, ensure_ascii=False))
            return 0
    generator = CSACheckerGenerator(
        rule,
        cases,
        rule_result_dir=args.result_dir,
        max_compiler_trys=args.max_compiler_trys,
        max_round=args.max_round,
        max_augmentation_tries=args.max_augmentation_tries,
        llvm_root=args.llvm_root,
        llvm_build=args.llvm_build,
        llm=llm,
        retrieval_mode=args.retrieval,
        embedding_model=args.embedding_model,
        embedding_cache=args.embedding_cache,
    )
    if args.first_checker_only:
        success, checker = generator.first_checker_generation()
        if success:
            rule.add_checker(checker)
            result = generator.run_all_test_cases()
        else:
            result = json.loads((generator.rule_dir / "checker_generation_result.json").read_text(encoding="utf-8"))
    else:
        generator.generate_checker()
        result = json.loads((generator.rule_dir / "checker_generation_result.json").read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["initial_case_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
