import copy
import json
import unittest
from pathlib import Path

from csa_official_checker_logic_extract.collect_checker_metaop import (
    ApiIndex,
    DatasetBuilder,
    SourceIndex,
    validate_dataset,
)
from csa_official_checker_logic_extract.rag_records import expand_logic_units
from csa_official_checker_logic_extract.static_analysis import StaticAnalyzer
from csa_official_checker_logic_extract.decompose_with_llm import run_decomposition


ROOT = Path(__file__).resolve().parents[2]
LLVM_ROOT = Path("/home/llvm/llvm-project")
API_JSON = ROOT / "csa_official_api_extract/csa_api.json"
DATASET = ROOT / "csa_official_checker_logic_extract/csa_meat_op.json"


@unittest.skipUnless(LLVM_ROOT.is_dir() and API_JSON.is_file(), "LLVM sources or Stage 1 data unavailable")
class GeneratedDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.sources = SourceIndex(LLVM_ROOT)
        cls.apis = ApiIndex(API_JSON)

    def checker(self, name):
        return next(item for item in self.data["checkers"] if item["implementation_class"] == name)

    def test_full_validation(self):
        validate_dataset(self.data, self.sources, self.apis.ids)

    def test_divzero_semantic_coverage(self):
        checker = self.checker("DivZeroChecker")
        self.assertEqual({item["name"] for item in checker["frontends"]}, {"DivZero", "TaintedDiv"})
        self.assertEqual(
            [item["kind"] for item in checker["logic_units"]],
            ["entry_filter", "value_modeling", "constraint_reasoning", "reporting", "reporting", "state_transition"],
        )
        implementation = "\n".join(item["meta_impl"] for item in checker["logic_units"])
        self.assertIn("assumeDual", implementation)
        self.assertIn("reportTaintBug", implementation)

    def test_stream_state_lifecycle_coverage(self):
        checker = self.checker("SimpleStreamChecker")
        self.assertEqual(checker["state_traits"][0]["name"], "StreamMap")
        implementation = "\n".join(item["meta_impl"] for item in checker["logic_units"])
        for expected in ["StreamState::getOpened", "StreamState::getClosed", "reportDoubleClose", "isLeaked", "checkPointerEscape"]:
            self.assertIn(expected, implementation)

    def test_malloc_family_and_cross_helper_units(self):
        checker = self.checker("MallocChecker")
        self.assertGreaterEqual(len(checker["frontends"]), 5)
        self.assertGreaterEqual(len(checker["callbacks"]), 8)
        self.assertTrue(any(any(span["role"] == "helper" for span in unit["source_spans"]) for unit in checker["logic_units"]))

    def test_rag_uses_id_and_preserves_duplicate_descriptions(self):
        duplicate = copy.deepcopy(self.data)
        units = duplicate["checkers"][0]["logic_units"]
        units[1]["meta_op"] = units[0]["meta_op"]
        records = expand_logic_units(duplicate)
        self.assertEqual(len(records), duplicate["metadata"]["logic_unit_count"])
        matching = [item for item in records if units[0]["meta_op"] in item["document"]]
        self.assertGreaterEqual(len(matching), 2)
        self.assertEqual(len({item["id"] for item in matching}), len(matching))
        self.assertTrue(all("meta_impl" in item["payload"] for item in records))

    def test_tampered_source_is_rejected(self):
        tampered = copy.deepcopy(self.data)
        tampered["checkers"][0]["logic_units"][0]["meta_impl"] += "\n// generated"
        with self.assertRaisesRegex(ValueError, "differs from source spans"):
            validate_dataset(tampered, self.sources, self.apis.ids)


class DeterminismTest(unittest.TestCase):
    @unittest.skipUnless(LLVM_ROOT.is_dir() and API_JSON.is_file(), "LLVM sources or Stage 1 data unavailable")
    def test_ids_are_stable(self):
        builder = DatasetBuilder(LLVM_ROOT, API_JSON)
        first = builder.build({"DivZeroChecker"})
        second = builder.build({"DivZeroChecker"})
        first["metadata"].pop("generated_at")
        second["metadata"].pop("generated_at")
        self.assertEqual(first, second)

    @unittest.skipUnless(LLVM_ROOT.is_dir(), "LLVM sources unavailable")
    def test_static_inventory_builds_callback_helper_slice(self):
        analyzer = StaticAnalyzer(LLVM_ROOT)
        inventory = analyzer.analyze_file(
            LLVM_ROOT / "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp"
        )
        checker = next(
            item for item in inventory["checker_classes"]
            if item["implementation_class"] == "DivZeroChecker"
        )
        self.assertEqual(checker["events"], ["check::PreStmt<BinaryOperator>"])
        div_slice = next(
            item for item in analyzer.callback_slices(inventory)
            if item["callback"]["method"] == "DivZeroChecker::checkPreStmt"
        )
        self.assertEqual(div_slice["symbols_in_call_order"][0], "DivZeroChecker::checkPreStmt")
        self.assertIn("DivZeroChecker::reportBug", div_slice["symbols_in_call_order"])
        self.assertEqual({item["name"] for item in inventory["registrations"]}, {"DivZero", "TaintedDiv"})

    @unittest.skipUnless(LLVM_ROOT.is_dir() and API_JSON.is_file(), "LLVM sources or Stage 1 data unavailable")
    def test_llm_plan_is_hydrated_from_source_not_model_code(self):
        analyzer = StaticAnalyzer(LLVM_ROOT)
        source = LLVM_ROOT / "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp"
        inventory = analyzer.analyze_file(source)
        callback = next(item for item in inventory["functions"] if item["symbol"] == "DivZeroChecker::checkPreStmt")
        response = {
            "summary": "Detect division by zero.",
            "analysis_mode": "path_sensitive",
            "logic_units": [{
                "slug": "callback",
                "kind": "detection",
                "meta_op": "Analyze a division denominator for zero.",
                "callback_context": ["DivZeroChecker::checkPreStmt"],
                "applies_to_frontends": ["DivZero", "TaintedDiv"],
                "depends_on": [],
                "api_names": [],
                "behavior": {
                    "preconditions": [], "state_reads": [], "state_writes": [],
                    "transitions": [], "reports": []
                },
                "source_selectors": [{
                    "role": "callback_segment",
                    "symbol": "DivZeroChecker::checkPreStmt",
                    "file": "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp",
                    "start_line": callback["start_line"],
                    "end_line": callback["end_line"],
                }],
            }],
        }
        plan = run_decomposition(
            analyzer,
            [source],
            "test prompt",
            lambda _prompt: json.dumps(response),
            retries=1,
        )
        canonical = DatasetBuilder(LLVM_ROOT, API_JSON).build_semantic_plan(plan)
        logic = canonical["checkers"][0]["logic_units"][0]
        expected = "\n".join(
            source.read_text(encoding="utf-8").splitlines()[callback["start_line"] - 1 : callback["end_line"]]
        )
        self.assertEqual(logic["meta_impl"], expected)


if __name__ == "__main__":
    unittest.main()
