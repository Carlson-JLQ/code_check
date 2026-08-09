import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from csa_generator import (
    CSACheckerGenerator,
    expected_diagnostics,
    parse_generated_source,
)
from entity.concreteProduct_CSA import Case_CSA, Checker_CSA, Rule_CSA
from main_csa import load_cases, load_rule
from prompt.csa_prompt.build_prompt import (
    build_augmentation_prompt,
    build_compiler_repair_prompt,
)


class CSAGeneratorTest(unittest.TestCase):
    def case(self, root, name, code):
        path = Path(root) / name
        path.write_text(code, encoding="utf-8")
        expected = expected_diagnostics(code)
        return Case_CSA(code, case_path=str(path), case_flag=not bool(expected),
                        expected_diagnostics=expected)

    def test_loads_shared_codeql_cases_as_ten_positive_and_ten_negative(self):
        root = Path(__file__).resolve().parents[2]
        cases = load_cases(root / "experiment/gjb8114/codeql_test_case/no_assignment_in_condition")
        self.assertEqual(len(cases), 20)
        self.assertEqual(sum(bool(expected_diagnostics(c.get_case_code())) for c in cases), 10)
        self.assertEqual(sum(c.get_flag() for c in cases), 10)

    def test_second_rule_derives_metadata_and_checker_identity(self):
        root = Path(__file__).resolve().parents[2]
        test_dir = root / "experiment/gjb8114/codeql_test_case/no_else_branch"
        cases = load_cases(test_dir)
        rule = load_rule(
            root / "experiment/gjb8114/rule_codeql/jgb8114_all_rules.json",
            "no-else-branch", test_dir, cases)
        generator = CSACheckerGenerator(rule, cases, retrieval_mode="lexical")
        self.assertEqual(rule.get_rule_id(), "gjb8114-r-1-4-1")
        self.assertEqual(rule.get_diagnostic(), "禁止省略 if-else if 语句的 else 分支")
        self.assertEqual(generator.checker_name, "GeneratedNoElseBranchChecker")
        self.assertEqual(generator.frontend, "gjb8114.NoElseBranch")

    def test_selects_only_first_non_skipped_negative(self):
        with tempfile.TemporaryDirectory() as root:
            skipped = self.case(root, "a.cpp", "// CHECK-MESSAGES: target\nint a(){return 0;}")
            selected = self.case(root, "b.cpp", "// CHECK-MESSAGES: target\nint b(){return 0;}")
            other = self.case(root, "c.cpp", "// CHECK-MESSAGES: target\nint c(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [skipped, selected, other], [skipped], root,
                retrieval_mode="lexical")
            self.assertIs(generator.select_initial_case(), selected)

    def test_expected_warning_parsers(self):
        self.assertEqual(expected_diagnostics(
            "// expected-warning{{Division by zero}}"), ["Division by zero"])
        self.assertEqual(expected_diagnostics(
            "// CHECK-MESSAGES: 禁止将赋值语句作为逻辑表达式 [gjb8114-r-1-6-3]"),
            ["禁止将赋值语句作为逻辑表达式"])

    def test_generated_source_parser_requires_only_cpp(self):
        answer = "```cpp\nextern \"C\" void clang_registerCheckers() {}\n```"
        cpp = parse_generated_source(answer)
        self.assertIn("clang_registerCheckers", cpp)

    def test_retrieval_uses_independent_csa_datasets(self):
        generator = CSACheckerGenerator(
            Rule_CSA(), [], rule_result_dir="/tmp", retrieval_mode="lexical")
        metaops, apis = generator.retrieve_context()
        self.assertTrue(metaops)
        self.assertTrue(apis)
        self.assertTrue(any(api.get("qualified_name") == "clang::ento::check::BranchCondition"
                            for api in apis))
        self.assertTrue(any(api.get("qualified_name") == "clang::ento::check::ASTCodeBody"
                            for api in apis))

    @patch("csa_generator.run_csa_analyzer")
    @patch("csa_generator.compile_csa_checker", return_value=(0, "ok", ""))
    def test_first_checker_and_full_result(self, _, analyzer):
        analyzer.return_value = (
            0, "", "x.cpp:1:1: warning: 禁止将赋值语句作为逻辑表达式 "
            "[gjb8114-r-1-6-3] [gjb8114.NoAssignmentInCondition]\n")
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(
                root, "negative.cpp",
                "int f(){int x=0;if(x=1)return 1;return 0;}\n"
                "// CHECK-MESSAGES: 禁止将赋值语句作为逻辑表达式 [gjb8114-r-1-6-3]")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative], rule_result_dir=root, retrieval_mode="lexical")
            success, checker = generator.first_checker_generation()
            self.assertTrue(success)
            generator.rule.add_checker(checker)
            result = generator.run_all_test_cases()
            self.assertTrue(result["all_cases_success"])
            self.assertTrue((Path(root) / "csa/no-assignment-in-condition/checker_generation_result.json").exists())

    @patch("csa_generator.run_csa_analyzer")
    @patch("csa_generator.compile_csa_checker", return_value=(1, "", "bad compile"))
    def test_compile_repair_is_bounded_without_llm(self, compiler, analyzer):
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "negative.cpp", "// CHECK-MESSAGES: target\nint f(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative], rule_result_dir=root,
                max_round=1, max_compiler_trys=3, retrieval_mode="lexical")
            success, _ = generator.first_checker_generation()
            self.assertFalse(success)
            self.assertEqual(compiler.call_count, 1)
            analyzer.assert_not_called()

    @patch("csa_generator.run_csa_analyzer")
    def test_result_separates_semantic_and_execution_failures(self, analyzer):
        analyzer.side_effect = [(0, "", ""), (2, "", "analyzer failed")]
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root,
                retrieval_mode="lexical")
            generator.generated = Checker_CSA(plugin_path="fake.so")
            results = generator.run_all_test_cases(write_result=False)
            self.assertEqual(results[0]["failure_category"], "false_negative")
            self.assertEqual(results[1]["failure_category"], "execution_failure")

    def test_offline_baseline_contains_independent_registration_names(self):
        generator = CSACheckerGenerator(Rule_CSA(), [], retrieval_mode="lexical")
        cpp = generator._fallback_source()
        self.assertIn("GeneratedNoAssignmentInConditionChecker", cpp)
        self.assertIn("gjb8114.NoAssignmentInCondition", cpp)
        self.assertIn("check::ASTCodeBody", cpp)
        self.assertNotIn('GeneratedNoAssignmentInConditionChecker.h', cpp)

    @patch("csa_generator.compile_csa_checker", side_effect=[
        (1, "", "first failure"), (0, "", "")])
    def test_compiler_failure_enters_bounded_repair_loop(self, compiler):
        with tempfile.TemporaryDirectory() as root:
            seed = CSACheckerGenerator(Rule_CSA(), [], retrieval_mode="lexical")
            cpp = seed._fallback_source()
            answer = f"```cpp\n{cpp}\n```"
            generator = CSACheckerGenerator(
                Rule_CSA(), [], rule_result_dir=root, max_compiler_trys=2,
                llm=lambda _: answer, retrieval_mode="lexical")
            context = generator.retrieve_context()
            success, *_ = generator._compile_with_repairs(
                cpp, Path(root) / "workspace", context, Path(root) / "artifacts")
            self.assertTrue(success)
            self.assertEqual(compiler.call_count, 2)

    @patch("csa_generator.compile_csa_checker", return_value=(0, "", ""))
    def test_positive_and_negative_augmentation_prompts_build_candidates(self, _):
        with tempfile.TemporaryDirectory() as root:
            seed = CSACheckerGenerator(Rule_CSA(), [], retrieval_mode="lexical")
            cpp = seed._fallback_source()
            answer = f"```cpp\n{cpp}\n```"
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root,
                llm=lambda _: answer, retrieval_mode="lexical")
            current = Checker_CSA(checker_code=cpp, passed_cases=[])
            negative_candidate = generator._augment_candidate(
                {"case_path": negative.get_case_path(), "failure_category": "false_negative"},
                current, Path(root) / "negative")
            positive_candidate = generator._augment_candidate(
                {"case_path": positive.get_case_path(), "failure_category": "false_positive"},
                current, Path(root) / "positive")
            self.assertEqual(negative_candidate.generation_kind, "augmentation_negative")
            self.assertEqual(positive_candidate.generation_kind, "augmentation_positive")

    def test_llm_provider_errors_are_retried_and_recorded(self):
        calls = []

        def failing_llm(_):
            calls.append(1)
            raise RuntimeError("upstream unavailable")

        with tempfile.TemporaryDirectory() as root:
            generator = CSACheckerGenerator(
                Rule_CSA(), [], rule_result_dir=root, llm=failing_llm,
                max_llm_tries=3, retrieval_mode="lexical")
            self.assertEqual(generator._invoke("prompt", Path(root) / "prompt.md"), "")
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(generator.llm_failures), 3)
            self.assertTrue((Path(root) / "prompt.errors.log").exists())

    def test_llm_usage_records_tokens_without_guessing_model_price(self):
        usage = SimpleNamespace(prompt_tokens=12, completion_tokens=5, total_tokens=17)

        with tempfile.TemporaryDirectory() as root:
            generator = CSACheckerGenerator(
                Rule_CSA(), [], rule_result_dir=root,
                llm=lambda _: ("answer", usage), retrieval_mode="lexical")
            self.assertEqual(generator._invoke("prompt"), "answer")
            self.assertEqual(generator.token_usage, {
                "prompt_tokens": 12,
                "completion_tokens": 5,
                "total_tokens": 17,
            })
            self.assertIsNone(generator.get_total_cost())

    def test_repair_and_augmentation_prompts_include_complete_failure_context(self):
        repair = build_compiler_repair_prompt(
            "current checker", "compiler error", "analysis", "apis", "metaops",
            "original rule and case", "template")
        self.assertIn("compiler error", repair)
        self.assertIn("current checker", repair)
        self.assertIn("original rule and case", repair)
        self.assertIn("BasicBugReport", repair)

        augmentation = build_augmentation_prompt(
            "negative", "rule", "current checker", "logic", "context",
            "passed cases", "failed case", "returncode: 2; stderr: crash")
        self.assertIn("returncode: 2; stderr: crash", augmentation)
        self.assertIn("expected/actual diagnostics", augmentation)


if __name__ == "__main__":
    unittest.main()
