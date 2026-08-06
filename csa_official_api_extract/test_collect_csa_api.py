import json
import unittest
from pathlib import Path

from collect_csa_api import CSAApiCollector


LLVM_ROOT = Path("/home/llvm/llvm-project")
HERE = Path(__file__).resolve().parent


class StaticExtractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not LLVM_ROOT.is_dir():
            raise unittest.SkipTest(f"LLVM source tree is unavailable: {LLVM_ROOT}")
        relative_files = [
            "clang/include/clang/StaticAnalyzer/Core/AnalyzerOptions.h",
            "clang/include/clang/StaticAnalyzer/Core/Checker.h",
            "clang/include/clang/StaticAnalyzer/Core/CheckerManager.h",
            "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CallEvent.h",
            "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h",
            "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState_Fwd.h",
            "clang/include/clang/StaticAnalyzer/Core/PathSensitive/SymExpr.h",
            "clang/include/clang/StaticAnalyzer/Core/PathSensitive/SVals.h",
            "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp",
        ]
        collector = CSAApiCollector(LLVM_ROOT)
        for relative_file in relative_files:
            collector.parse_file(LLVM_ROOT / relative_file)
        result = collector.result()
        cls.types = result["types"]
        cls.apis = result["apis"]

    def one_type(self, qualified_name: str) -> dict:
        matches = [
            item for item in self.types if item["qualified_name"] == qualified_name
        ]
        self.assertEqual(len(matches), 1, qualified_name)
        return matches[0]

    def test_checker_context_emit_report_is_reusable(self) -> None:
        matches = [
            item
            for item in self.apis
            if item["qualified_name"] == "clang::ento::CheckerContext::emitReport"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(
            matches[0]["required_includes"],
            ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"],
        )
        self.assertEqual(matches[0]["availability"], "public_framework")
        self.assertIs(matches[0]["reusable"], True)

    def test_cpp_checker_symbols_are_excluded(self) -> None:
        forbidden = {
            "checkPreStmt",
            "reportBug",
            "reportTaintBug",
            "getDenomExpr",
            "registerDivZeroChecker",
            "shouldRegisterDivZeroChecker",
            "registerTaintedDivChecker",
            "shouldRegisterTaintedDivChecker",
        }
        self.assertFalse(forbidden.intersection(item["name"] for item in self.apis))
        self.assertFalse(
            any("DivZeroChecker" in item["qualified_name"] for item in self.types)
        )

    def test_enums(self) -> None:
        scoped = self.one_type("clang::ExplorationStrategyKind")
        self.assertEqual(scoped["kind"], "enum")
        self.assertIs(scoped["scoped"], True)
        self.assertIn("DFS", [item["name"] for item in scoped["enumerators"]])

        unscoped = self.one_type("clang::ento::PointerEscapeKind")
        self.assertEqual(unscoped["kind"], "enum")
        self.assertIs(unscoped["scoped"], False)
        self.assertIn(
            "PSK_DirectEscapeOnCall",
            [item["name"] for item in unscoped["enumerators"]],
        )

    def test_type_aliases(self) -> None:
        symbol_ref = self.one_type("clang::ento::SymbolRef")
        self.assertEqual(symbol_ref["alias_syntax"], "using")
        self.assertEqual(symbol_ref["target_type"], "const SymExpr *")

        state_ref = self.one_type("clang::ento::ProgramStateRef")
        self.assertEqual(state_ref["alias_syntax"], "typedef")
        self.assertEqual(
            state_ref["target_type"], "IntrusiveRefCntPtr<const ProgramState>"
        )

    def test_template_parameters(self) -> None:
        call_event_ref = self.one_type("clang::ento::CallEventRef")
        self.assertEqual(
            call_event_ref["template_parameters"],
            [
                {
                    "name": "T",
                    "kind": "type",
                    "declared_type": None,
                    "is_pack": False,
                    "default_value": "CallEvent",
                }
            ],
        )
        self.assertTrue(call_event_ref["source"]["code"].startswith("template <"))

        checker = self.one_type("clang::ento::Checker")
        self.assertEqual(checker["template_parameters"][0]["name"], "CHECKs")
        self.assertIs(checker["template_parameters"][0]["is_pack"], True)

    def test_def_macro_recovery_preserves_access_filtering(self) -> None:
        self.one_type("clang::ento::SVal")
        self.assertTrue(
            any(
                item["qualified_name"] == "clang::ento::SVal::castAs"
                for item in self.apis
            )
        )
        self.assertFalse(any(item["name"] == "castDataAs" for item in self.apis))


class GeneratedJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((HERE / "csa_api.json").read_text(encoding="utf-8"))

    def test_schema_and_public_record_invariants(self) -> None:
        self.assertEqual(self.data["metadata"]["schema_version"], "1.1")
        self.assertEqual(
            self.data["metadata"]["input_policy"], "public_reusable_only"
        )
        for record in self.data["types"] + self.data["apis"]:
            self.assertEqual(record["availability"], "public_framework")
            self.assertIs(record["reusable"], True)
            self.assertTrue(record["required_includes"])
            self.assertTrue(
                all(
                    include.startswith("clang/StaticAnalyzer/")
                    for include in record["required_includes"]
                )
            )
            self.assertNotIn(record.get("access"), {"private", "protected"})


if __name__ == "__main__":
    unittest.main()
