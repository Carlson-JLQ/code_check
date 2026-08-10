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
    parse_json_payload,
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

    def test_initial_generation_records_only_configured_negative_candidate_budget(self):
        with tempfile.TemporaryDirectory() as root:
            cases = [self.case(root, f"n{i}.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
                     for i in range(5)]
            generator = CSACheckerGenerator(
                Rule_CSA(), cases, rule_result_dir=root,
                max_initial_negative_cases=3, max_round=1,
                retrieval_mode="lexical")
            with patch("csa_generator.compile_csa_checker", return_value=(1, "", "compile failed")):
                success, _ = generator.first_checker_generation()
            self.assertFalse(success)
            self.assertEqual(len(generator.initial_candidate_results), 3)
            output = json.loads((Path(root) / "csa/no-assignment-in-condition/checker_generation_result.json")
                                .read_text(encoding="utf-8"))
            self.assertEqual(output["performance"], "0/3")
            self.assertEqual(output["initial_candidate_amount"], 3)
            self.assertTrue(all(item["failure_category"] == "compile_failure"
                                for item in output["failed_case_list"]))

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

    def test_augmentation_identity_does_not_require_literal_rule_text(self):
        generator = CSACheckerGenerator(Rule_CSA(), [], retrieval_mode="lexical")
        template = generator._template_source()
        self.assertTrue(generator._checker_identity_valid(template))

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

    def test_semantic_augmentation_accepts_strictly_improved_candidate(self):
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root,
                max_augmentation_tries=1, retrieval_mode="lexical")
            initial = Checker_CSA(
                checker_code="initial", plugin_path=str(Path(root) / "initial.so"), version=1)
            initial.set_passed_cases([positive])
            candidate = Checker_CSA(
                checker_code="improved", plugin_path=str(Path(root) / "candidate.so"), version=2,
                generation_kind="augmentation_negative")
            baseline = [
                self._case_result(negative, False, "false_negative"),
                self._case_result(positive, True),
            ]
            improved = [self._case_result(negative, True), self._case_result(positive, True)]
            generator.generated = initial
            generator.rule.add_checker(initial)
            with patch.object(generator, "run_all_test_cases", side_effect=[baseline, improved]), \
                    patch.object(generator, "_augment_candidate", return_value=candidate), \
                    patch.object(generator, "_run_case", return_value=self._case_result(negative, True)):
                result = generator.checker_augmentation(initial)
            self.assertIs(result, candidate)
            self.assertIs(generator.generated, candidate)
            self.assertEqual(generator.accepted_augmentation_amount, 1)
            self.assertEqual(generator.rollback_count, 0)
            manifest = Path(root) / "csa/no-assignment-in-condition/augmentation/attempt_1/candidate_manifest.json"
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["status"], "accepted")

    def test_later_regression_keeps_last_accepted_version(self):
        with tempfile.TemporaryDirectory() as root:
            first = self.case(root, "n1.cpp", "// CHECK-MESSAGES: target\nint n1(){return 0;}")
            second = self.case(root, "n2.cpp", "// CHECK-MESSAGES: target\nint n2(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [first, second, positive], rule_result_dir=root,
                max_augmentation_tries=2, retrieval_mode="lexical")
            initial = Checker_CSA(checker_code="v1", plugin_path="v1.so", version=1)
            version_two = Checker_CSA(
                checker_code="v2", plugin_path="v2.so", version=2,
                generation_kind="augmentation_negative")
            rejected_v3 = Checker_CSA(
                checker_code="v3", plugin_path="v3.so", version=3,
                generation_kind="augmentation_negative")
            baseline = [
                self._case_result(first, False, "false_negative"),
                self._case_result(second, False, "false_negative"),
                self._case_result(positive, True),
            ]
            v2_results = [
                self._case_result(first, True),
                self._case_result(second, False, "false_negative"),
                self._case_result(positive, True),
            ]
            regressed_v3 = [
                self._case_result(first, False, "false_negative"),
                self._case_result(second, True),
                self._case_result(positive, True),
            ]
            generator.generated = initial
            generator.rule.add_checker(initial)
            with patch.object(generator, "run_all_test_cases",
                              side_effect=[baseline, v2_results, regressed_v3]), \
                    patch.object(generator, "_augment_candidate",
                                 side_effect=[version_two, rejected_v3]), \
                    patch.object(generator, "_run_case",
                                 side_effect=[self._case_result(first, True),
                                              self._case_result(second, True)]):
                result = generator.checker_augmentation(initial)
            self.assertIs(result, version_two)
            self.assertIs(generator.generated, version_two)
            self.assertEqual(generator.accepted_augmentation_amount, 1)
            self.assertEqual(generator.rejected_augmentation_amount, 1)
            self.assertEqual(generator.rollback_count, 1)
            output = json.loads((Path(root) / "csa/no-assignment-in-condition/checker_generation_result.json")
                                .read_text(encoding="utf-8"))
            self.assertEqual(output["active_version"], 2)
            self.assertTrue(output["rollback_performed"])

    def test_all_rejected_augmentations_fall_back_to_initial_checker(self):
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root,
                max_augmentation_tries=1, retrieval_mode="lexical")
            initial = Checker_CSA(checker_code="v1", plugin_path="v1.so", version=1)
            rejected = Checker_CSA(
                checker_code="candidate", plugin_path="candidate.so", version=2,
                generation_kind="augmentation_negative")
            baseline = [
                self._case_result(negative, False, "false_negative"),
                self._case_result(positive, True),
            ]
            generator.generated = initial
            generator.rule.add_checker(initial)
            with patch.object(generator, "run_all_test_cases", return_value=baseline), \
                    patch.object(generator, "_augment_candidate", return_value=rejected), \
                    patch.object(generator, "_run_case",
                                 return_value=self._case_result(
                                     negative, False, "false_negative")):
                result = generator.checker_augmentation(initial)
            self.assertIs(result, initial)
            self.assertIs(generator.generated, initial)
            self.assertEqual(generator.accepted_augmentation_amount, 0)
            self.assertEqual(generator.rollback_count, 1)
            output = json.loads((Path(root) / "csa/no-assignment-in-condition/checker_generation_result.json")
                                .read_text(encoding="utf-8"))
            self.assertEqual(output["baseline_version"], 1)
            self.assertEqual(output["active_version"], 1)
            self.assertEqual(output["best_version"], 1)

    def _case_result(self, case, success, failure_category=None):
        return {
            "case_path": str(case.get_case_path()),
            "case_type": "negative" if case.expected_diagnostics else "positive",
            "expected_diagnostics": case.expected_diagnostics,
            "actual_diagnostics": ["target"] if success and case.expected_diagnostics else [],
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "success": success,
            "failure_category": failure_category,
        }

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

    def test_logic_payload_survives_a_prose_preamble(self):
        answer = (
            "I'm extracting the detection units from the rule text, then I'll "
            'normalize them into JSON.[{"intent": "flag anonymous records", '
            '"trigger": "check::ASTDecl<RecordDecl>"}]'
        )
        self.assertEqual(
            parse_json_payload(answer),
            [{"intent": "flag anonymous records", "trigger": "check::ASTDecl<RecordDecl>"}])
        self.assertIsNone(parse_json_payload("no payload at all"))

    def test_logic_extraction_failure_is_recorded_without_naming_a_callback(self):
        with tempfile.TemporaryDirectory() as root:
            generator = CSACheckerGenerator(
                Rule_CSA(), [], rule_result_dir=root, retrieval_mode="lexical",
                llm=lambda _: "sorry, no JSON here")
            logics = generator.run_logic_for_negative_case("rule", "int f(){}", Path(root))
            self.assertEqual(len(generator.logic_parse_failures), 1)
            # A hardcoded check::ASTCodeBody turned every parse failure into a
            # checker bound to the wrong callback.
            self.assertNotIn("check::ASTCodeBody", logics[0]["trigger"])

    def test_gate_violations_name_the_clause_that_fired(self):
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root, retrieval_mode="lexical")
            baseline = [
                self._case_result(negative, False, "false_negative"),
                self._case_result(positive, True),
            ]
            crashed = [
                self._case_result(negative, True),
                self._case_result(positive, False, "execution_failure"),
            ]
            violations, old_score, new_score = generator._gate_violations(baseline, crashed)
            self.assertEqual((old_score, new_score), (1, 1))
            self.assertTrue(any("score did not improve" in item for item in violations))
            self.assertTrue(any("crash" in item and "p.cpp" in item for item in violations))

    def test_higher_scoring_rejected_candidate_is_retained_and_promoted(self):
        """A 19/20 with zero regressions must not lose to the 18/20 that passed the gate."""
        with tempfile.TemporaryDirectory() as root:
            first = self.case(root, "n1.cpp", "// CHECK-MESSAGES: target\nint n1(){return 0;}")
            second = self.case(root, "n2.cpp", "// CHECK-MESSAGES: target\nint n2(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [first, second, positive], rule_result_dir=root,
                max_augmentation_tries=1, max_execution_repair_tries=0,
                retrieval_mode="lexical")
            initial = Checker_CSA(checker_code="v1", plugin_path="v1.so", version=1)
            rejected = Checker_CSA(
                checker_code="v2-better", plugin_path="v2.so", version=2,
                generation_kind="augmentation_negative")
            baseline = [
                self._case_result(first, False, "false_negative"),
                self._case_result(second, False, "false_negative"),
                self._case_result(positive, True),
            ]
            # Fixes both negatives, regresses nothing, but crashes the analyzer
            # on a case that used to pass: rejected by the gate, still the best.
            better = [
                self._case_result(first, True),
                self._case_result(second, True),
                self._case_result(positive, False, "execution_failure"),
            ]
            generator.generated = initial
            generator.rule.add_checker(initial)
            with patch.object(generator, "run_all_test_cases", side_effect=[baseline, better]), \
                    patch.object(generator, "_augment_candidate", return_value=rejected), \
                    patch.object(generator, "_run_case", return_value=self._case_result(first, True)):
                generator.checker_augmentation(initial)
            self.assertEqual(generator.rejected_augmentation_amount, 1)
            self.assertEqual(generator.accepted_augmentation_amount, 0)
            self.assertIs(generator.best_candidate, rejected)
            self.assertEqual(generator.best_score, 2)
            self.assertTrue(generator.promoted_from_best)
            self.assertIs(generator.generated, rejected)
            retained = Path(root) / "csa/no-assignment-in-condition/augmentation/best_candidate/checker.cpp"
            self.assertEqual(retained.read_text(encoding="utf-8"), "v2-better")
            result = json.loads(
                (Path(root) / "csa/no-assignment-in-condition/checker_generation_result.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(result["best_score"], 2)
            self.assertEqual(result["final_execution_failure_amount"], 1)
            self.assertTrue(result["promoted_from_best"])

    def test_promotion_can_be_refused_when_the_best_candidate_crashes(self):
        with tempfile.TemporaryDirectory() as root:
            first = self.case(root, "n1.cpp", "// CHECK-MESSAGES: target\nint n1(){return 0;}")
            second = self.case(root, "n2.cpp", "// CHECK-MESSAGES: target\nint n2(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [first, second, positive], rule_result_dir=root,
                max_augmentation_tries=1, max_execution_repair_tries=0,
                promote_with_execution_failures=False, retrieval_mode="lexical")
            initial = Checker_CSA(checker_code="v1", plugin_path="v1.so", version=1)
            rejected = Checker_CSA(
                checker_code="v2-better", plugin_path="v2.so", version=2,
                generation_kind="augmentation_negative")
            baseline = [
                self._case_result(first, False, "false_negative"),
                self._case_result(second, False, "false_negative"),
                self._case_result(positive, True),
            ]
            better = [
                self._case_result(first, True),
                self._case_result(second, True),
                self._case_result(positive, False, "execution_failure"),
            ]
            generator.generated = initial
            generator.rule.add_checker(initial)
            with patch.object(generator, "run_all_test_cases", side_effect=[baseline, better]), \
                    patch.object(generator, "_augment_candidate", return_value=rejected), \
                    patch.object(generator, "_run_case", return_value=self._case_result(first, True)):
                generator.checker_augmentation(initial)
            self.assertFalse(generator.promoted_from_best)
            self.assertIs(generator.generated, initial)
            self.assertIs(generator.best_candidate, rejected)

    def test_compile_failures_do_not_consume_the_semantic_repair_budget(self):
        with tempfile.TemporaryDirectory() as root:
            negative = self.case(root, "n.cpp", "// CHECK-MESSAGES: target\nint n(){return 0;}")
            positive = self.case(root, "p.cpp", "int p(){return 0;}")
            generator = CSACheckerGenerator(
                Rule_CSA(), [negative, positive], rule_result_dir=root,
                max_augmentation_tries=4, max_semantic_repair_tries=1,
                max_technical_retries_per_case=2, max_execution_repair_tries=0,
                retrieval_mode="lexical")
            initial = Checker_CSA(checker_code="v1", plugin_path="v1.so", version=1)
            baseline = [
                self._case_result(negative, False, "false_negative"),
                self._case_result(positive, True),
            ]
            generator.generated = initial
            generator.rule.add_checker(initial)

            def failed_build(*args, **kwargs):
                generator._last_augmentation_build = {"reason": "compile_failed", "detail": None}
                return None

            with patch.object(generator, "run_all_test_cases", return_value=baseline), \
                    patch.object(generator, "_augment_candidate", side_effect=failed_build):
                generator.checker_augmentation(initial)
            # Two technical retries, then the case is out of technical budget -
            # its single semantic try was never spent on a compiler error.
            self.assertEqual(generator.augmentation_attempts, 2)
            self.assertEqual(generator.termination_reason, "semantic_repair_limit_reached")


if __name__ == "__main__":
    unittest.main()
