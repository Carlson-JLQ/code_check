"""CodeQL-shaped generation lifecycle for standalone CSA checker plugins."""

import json
import re
import time
from pathlib import Path
from typing import Iterable, Optional

from entity.concreteProduct_CSA import Case_CSA, Checker_CSA, Rule_CSA
from plateform.csa import compile_csa_checker, run_csa_analyzer
from prompt.csa_prompt.build_prompt import (
    build_augmentation_logic_prompt,
    build_augmentation_prompt,
    build_compiler_analysis_prompt,
    build_compiler_repair_prompt,
    build_first_checker_prompt,
    build_logic_prompt,
)
from retriever.csa_embedding import CSAEmbeddingRetriever, DEFAULT_MODEL


CHECK_MESSAGE_RE = re.compile(r"CHECK-MESSAGES\s*:\s*(.*?)(?=\s*\[[^]]+\]\s*$|$)", re.M)
EXPECTED_RE = re.compile(r"expected-(?:warning|error|note)\s*\{\{\s*([^}]*?)\s*\}\}")


def expected_diagnostics(source: str):
    """Read both LLVM expected-* and the repository's CodeQL CHECK-MESSAGES."""
    expected = EXPECTED_RE.findall(source)
    expected.extend(match.strip() for match in CHECK_MESSAGE_RE.findall(source))
    return [item for item in expected if item]


def is_negative(case: Case_CSA) -> bool:
    return bool(expected_diagnostics(case.get_case_code()))


def parse_generated_source(answer: str):
    blocks = re.findall(r"```(?:cpp|c\+\+|cc|c)?\s*\n(.*?)```", answer or "", re.S | re.I)
    cpp = next((block for block in blocks if "clang_registerCheckers" in block), "")
    if not cpp and blocks:
        cpp = blocks[0]
    if not cpp and "clang_registerCheckers" in (answer or ""):
        cpp = answer
    return cpp.strip()


def _no_assignment_source(checker_name, frontend, diagnostic, rule_id):
    return f'''#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {{
const BinaryOperator *findAssignment(const Stmt *S) {{
  if (!S)
    return nullptr;
  if (const auto *B = dyn_cast<BinaryOperator>(S)) {{
    if (B->isAssignmentOp())
      return B;
  }}
  for (const Stmt *Child : S->children())
    if (const BinaryOperator *Found = findAssignment(Child))
      return Found;
  return nullptr;
}}

class {checker_name} : public Checker<check::ASTCodeBody> {{
  const BugType BT{{this, "{diagnostic}", "GJB8114"}};

  void inspectCondition(const Expr *Condition, AnalysisDeclContext *ADC,
                        BugReporter &BR) const {{
    const BinaryOperator *Assignment = findAssignment(Condition);
    if (!Assignment)
      return;
    PathDiagnosticLocation Location(Assignment->getExprLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "{diagnostic} [{rule_id}]", Location);
    Report->addRange(Assignment->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }}

  void inspectStatements(const Stmt *S, AnalysisDeclContext *ADC,
                         BugReporter &BR) const {{
    if (!S)
      return;
    if (const auto *If = dyn_cast<IfStmt>(S))
      inspectCondition(If->getCond(), ADC, BR);
    else if (const auto *While = dyn_cast<WhileStmt>(S))
      inspectCondition(While->getCond(), ADC, BR);
    else if (const auto *Do = dyn_cast<DoStmt>(S))
      inspectCondition(Do->getCond(), ADC, BR);
    else if (const auto *For = dyn_cast<ForStmt>(S))
      inspectCondition(For->getCond(), ADC, BR);
    for (const Stmt *Child : S->children())
      inspectStatements(Child, ADC, BR);
  }}

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {{
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    inspectStatements(D->getBody(), ADC, BR);
  }}
}};
}} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {{
  Registry.addChecker<{checker_name}>(
      "{frontend}", "Detect assignment operations in branch conditions");
}}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
'''


def _plugin_template_source(checker_name, frontend):
    return f'''#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {{
class {checker_name} : public Checker<check::ASTCodeBody> {{
  const BugType BT{{this, "Generated GJB8114 violation", "GJB8114"}};

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {{
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "Replace with the required diagnostic text", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }}

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {{
    (void)D;
    (void)AM;
    (void)BR;
    // Implement the retrieved rule logic here.
  }}
}};
}} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {{
  Registry.addChecker<{checker_name}>(
      "{frontend}", "Generated GJB8114 checker");
}}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
'''


def _pascal_case(value):
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[^A-Za-z0-9]+", value) if part)


def _tokens(value):
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_:.-]+", value.lower()))


def _compact_record(record, code_limit=2500):
    """Keep retrieved context useful without feeding entire framework files."""
    def compact(value, key="", depth=0):
        if depth > 5:
            return "..."
        if isinstance(value, str):
            limit = code_limit if key in {"code", "source", "raw_source", "definition"} else 1200
            return value[:limit]
        if isinstance(value, list):
            return [compact(item, key, depth + 1) for item in value[:20]]
        if isinstance(value, dict):
            return {child_key: compact(child, child_key, depth + 1)
                    for child_key, child in value.items()
                    if child_key not in {"logic_units", "declarations"}}
        return value

    return compact(record)


class CSACheckerGenerator:
    def __init__(
        self,
        rule: Rule_CSA,
        all_test_cases: Iterable[Case_CSA] = (),
        skipped_test_cases=(),
        rule_result_dir="result-generation",
        max_compiler_trys=2,
        max_round=2,
        max_augmentation_tries=4,
        max_llm_tries=3,
        api_json=None,
        metaop_json=None,
        llvm_root="/home/llvm/llvm-project",
        compiler=None,
        analyzer=None,
        llm=None,
        llvm_build="/home/checker/llvm-build",
        retrieval_mode="embedding",
        embedding_model=DEFAULT_MODEL,
        embedding_cache=None,
        embedding_retriever=None,
    ):
        self.rule = self.RULE = rule
        rule_class_name = _pascal_case(rule.get_rule_name())
        self.checker_name = f"Generated{rule_class_name}Checker"
        self.frontend = f"gjb8114.{rule_class_name}"
        self.cases = self.all_Test_Case_List = list(all_test_cases or [])
        self.skipped = {str(case.get_case_path()) for case in (skipped_test_cases or [])}
        self.skipped_Test_Cases = []
        root = Path(rule_result_dir)
        self.rule_dir = root / "csa" / rule.get_rule_name()
        self.first_dir = self.rule_dir / "first_checker"
        self.debug_prompt_dir = self.rule_dir / "debug_prompt"
        self.max_compiler_trys = max(0, int(max_compiler_trys))
        self.max_round = max(1, int(max_round))
        self.max_augmentation_tries = max(0, int(max_augmentation_tries))
        self.max_llm_tries = max(1, int(max_llm_tries))
        self.llvm_root, self.llvm_build = Path(llvm_root), Path(llvm_build)
        self.compiler = compiler or str(self.llvm_build / "bin/clang++")
        self.analyzer = analyzer or str(self.llvm_build / "bin/clang")
        self.llm = llm
        base = Path(__file__).resolve().parents[1]
        self.api_path = Path(api_json or base / "csa_official_api_extract/csa_api.json")
        self.metaop_path = Path(metaop_json or base / "csa_official_checker_logic_extract/csa_meat_op.json")
        self.retrieval_mode = retrieval_mode
        if retrieval_mode not in {"embedding", "lexical"}:
            raise ValueError("retrieval_mode must be 'embedding' or 'lexical'")
        self.embedding_model = str(embedding_model)
        self.embedding_cache = Path(embedding_cache or base / "src/embedding_db/csa")
        self.embedding_retriever = embedding_retriever
        self.retrieval_stats = None
        self.generated: Optional[Checker_CSA] = None
        self.initial_case: Optional[Case_CSA] = None
        self.compile_attempts = 0
        self.generation_attempts = 0
        self.augmentation_attempts = 0
        # Provider pricing varies by model and is not part of the MetaOp config.
        # Keep exact token accounting and leave monetary cost unset unless a
        # caller adds an explicit pricing policy.
        self.total_cost = None
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self.llm_failures = []
        self.last_results = []
        self.termination_reason = "not_started"

    def get_total_cost(self):
        return self.total_cost

    def select_initial_case(self):
        return next((case for case in self.cases if not case.skipped
                     and str(case.get_case_path()) not in self.skipped
                     and is_negative(case)), None)

    def _candidate_negatives(self):
        return [case for case in self.cases if is_negative(case) and not case.skipped
                and str(case.get_case_path()) not in self.skipped]

    def _write_text(self, path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def _write_json(self, path, value):
        self._write_text(path, json.dumps(value, indent=2, ensure_ascii=False))

    def _invoke(self, prompt, artifact_path=None):
        if artifact_path:
            self._write_text(artifact_path, prompt)
        if not self.llm:
            return ""
        last = ""
        errors = []
        for attempt in range(1, self.max_llm_tries + 1):
            try:
                response = self.llm(prompt)
            except Exception as exc:
                message = f"attempt {attempt}: {type(exc).__name__}: {exc}"
                errors.append(message)
                self.llm_failures.append(message)
                if attempt < self.max_llm_tries:
                    time.sleep(min(2 ** (attempt - 1), 4))
                continue
            if isinstance(response, tuple):
                last = response[0]
                if len(response) > 1:
                    usage = response[1]
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                    total_tokens = getattr(usage, "total_tokens", 0) or (
                        prompt_tokens + completion_tokens
                    )
                    self.token_usage["prompt_tokens"] += prompt_tokens
                    self.token_usage["completion_tokens"] += completion_tokens
                    self.token_usage["total_tokens"] += total_tokens
            else:
                last = response
            if last:
                break
        if artifact_path:
            self._write_text(Path(artifact_path).with_suffix(".answer.md"), last or "")
            if errors:
                self._write_text(Path(artifact_path).with_suffix(".errors.log"), "\n".join(errors) + "\n")
        return last or ""

    def run_logic_for_negative_case(self, rule_description, case_code, artifact_dir=None):
        prompt = build_logic_prompt(rule_description, case_code)
        answer = self._invoke(prompt, Path(artifact_dir) / "logic_prompt.md" if artifact_dir else None)
        if answer:
            cleaned = re.sub(r"```json|```", "", answer, flags=re.I).strip()
            try:
                value = json.loads(cleaned)
                return value if isinstance(value, list) else [value]
            except json.JSONDecodeError:
                pass
        return [{
            "intent": f"implement the rule: {rule_description}",
            "trigger": "check::ASTCodeBody",
            "constraints": ["inspect the complete AST", "emit the configured diagnostic"],
            "api_search_terms": ["ASTCodeBody", "Stmt", "BugType", "CheckerRegistry"],
        }]

    def _lexical_context(self, logics=None, limit=8):
        query = " ".join([
            self.rule.get_rule_name(), self.rule.get_rule_description(),
            json.dumps(logics or [], ensure_ascii=False),
            "ASTCodeBody Stmt Decl BugType CheckerRegistry",
        ])
        query_tokens = _tokens(query)
        meta_data = json.loads(self.metaop_path.read_text(encoding="utf-8"))
        meta_records = []
        for checker in meta_data.get("checkers", []):
            for unit in checker.get("logic_units", []):
                record = {
                    "checker": checker.get("implementation_class"),
                    "frontends": checker.get("frontends", []),
                    **unit,
                }
                score = len(query_tokens & _tokens(json.dumps(record, ensure_ascii=False)))
                meta_records.append((score, record))
        meta_records.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
        selected_meta = [_compact_record(record) for _, record in meta_records[:limit]]

        api_data = json.loads(self.api_path.read_text(encoding="utf-8"))
        api_records = list(api_data.get("apis", api_data.get("api", api_data.get("functions", []))))
        # Callback interfaces such as check::BranchCondition are types rather
        # than functions in the official extraction output.
        api_records.extend(api_data.get("types", []))
        required = {
            "clang::ento::check::ASTCodeBody",
            "clang::ento::check::BranchCondition",
        }
        scored_api = []
        for record in api_records:
            serialized = json.dumps(record, ensure_ascii=False)
            score = len(query_tokens & _tokens(serialized))
            if record.get("qualified_name") in required:
                score += 100
            if score:
                scored_api.append((score, record))
        scored_api.sort(key=lambda item: (-item[0], str(item[1].get("qualified_name", ""))))
        selected_api = [_compact_record(record) for _, record in scored_api[:limit]]
        return selected_meta, selected_api

    def retrieve_context(self, logics=None, limit=8):
        """Retrieve generation context through the configured CSA index."""
        if self.retrieval_mode == "lexical":
            self.retrieval_stats = {"mode": "lexical", "fallback": True}
            return self._lexical_context(logics, limit)
        if self.embedding_retriever is None:
            self.embedding_retriever = CSAEmbeddingRetriever(
                self.metaop_path,
                self.api_path,
                self.embedding_cache,
                self.embedding_model,
            )
        query = " ".join([
            self.rule.get_rule_name(), self.rule.get_rule_description(),
            json.dumps(logics or [], ensure_ascii=False),
        ])
        metaops, api_refs = self.embedding_retriever.retrieve(
            query, metaop_top_k=max(1, limit // 2), api_top_k=limit)
        self.retrieval_stats = {"mode": "embedding", **self.embedding_retriever.stats()}

        # MetaOps carry precise API references. Add those records after the
        # semantic Top-K so generation receives both semantic and structural context.
        referenced_names = {
            ref.get("qualified_name")
            for unit in metaops
            for ref in unit.get("api_refs", [])
            if ref.get("qualified_name")
        }
        required_names = {
            "clang::ento::check::ASTCodeBody",
            "clang::ento::check::BranchCondition",
        }
        wanted_names = referenced_names | required_names
        present = {item.get("qualified_name") for item in api_refs}
        if not wanted_names.issubset(present):
            api_data = json.loads(self.api_path.read_text(encoding="utf-8"))
            for record in [*api_data.get("apis", []), *api_data.get("types", [])]:
                name = record.get("qualified_name")
                if name in wanted_names and name not in present:
                    item = _compact_record(record)
                    item["_retrieval"] = "metaop_api_ref" if name in referenced_names else "required_framework"
                    api_refs.append(item)
                    present.add(name)
        return [_compact_record(item) for item in metaops], [_compact_record(item) for item in api_refs]

    def _fallback_source(self):
        if self.rule.get_rule_name() != "no-assignment-in-condition":
            return ""
        return _no_assignment_source(
            self.checker_name, self.frontend, self.rule.get_diagnostic(), self.rule.get_rule_id())

    def _template_source(self):
        return _plugin_template_source(self.checker_name, self.frontend)

    def _save_source(self, workspace, cpp):
        workspace = Path(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        cpp_path = workspace / f"{self.checker_name}.cpp"
        self._write_text(cpp_path, cpp)
        return cpp_path, workspace / f"{self.checker_name}.so"

    def _compile_with_repairs(self, cpp, workspace, context, artifact_dir,
                              generation_context=""):
        cpp_path, plugin_path = self._save_source(workspace, cpp)
        current_cpp = cpp
        for repair_number in range(self.max_compiler_trys + 1):
            self.compile_attempts += 1
            rc, stdout, stderr = compile_csa_checker(
                cpp_path, workspace, self.llvm_root, self.compiler, self.llvm_build,
                plugin_name=plugin_path.name)
            compile_dir = Path(artifact_dir) / ("first_generation" if repair_number == 0
                                                else f"compiler_failed_try_{repair_number}")
            self._write_text(compile_dir / "compile.stdout", stdout)
            self._write_text(compile_dir / "compile.stderr", stderr)
            self._write_text(compile_dir / "generated_checker.cpp", current_cpp)
            if rc == 0:
                return True, current_cpp, plugin_path, rc, stdout, stderr
            if not self.llm or repair_number >= self.max_compiler_trys:
                break
            compiler_output = stdout + "\n" + stderr
            analysis_prompt = build_compiler_analysis_prompt(
                current_cpp, compiler_output,
                json.dumps(context[1], ensure_ascii=False),
                json.dumps(context[0], ensure_ascii=False), generation_context)
            analysis = self._invoke(analysis_prompt, compile_dir / "compiler_analysis_prompt.md")
            repair_prompt = build_compiler_repair_prompt(
                current_cpp, compiler_output, analysis,
                json.dumps(context[1], ensure_ascii=False), json.dumps(context[0], ensure_ascii=False),
                generation_context, self._template_source())
            answer = self._invoke(repair_prompt, compile_dir / "compiler_repair_prompt.md")
            repaired_cpp = parse_generated_source(answer)
            if not repaired_cpp:
                break
            current_cpp = repaired_cpp
            cpp_path, plugin_path = self._save_source(workspace, current_cpp)
        return False, current_cpp, plugin_path, rc, stdout, stderr

    def _target_diagnostics(self, output):
        marker = self.rule.get_rule_id().lower()
        frontend = self.frontend.lower()
        diagnostic = self.rule.get_diagnostic().lower()
        return [line.strip() for line in output.splitlines()
                if "warning:" in line.lower() and
                (marker in line.lower() or frontend in line.lower() or diagnostic in line.lower())]

    def _run_case(self, case, checker=None):
        checker = checker or self.generated
        rc, stdout, stderr = run_csa_analyzer(
            case.get_case_path(), checker.frontend, self.analyzer, checker.plugin_path)
        combined = stdout + stderr
        actual = self._target_diagnostics(combined)
        expected = expected_diagnostics(case.get_case_code())
        negative = bool(expected)
        if rc != 0:
            passed, category = False, "execution_failure"
        elif negative and not actual:
            passed, category = False, "false_negative"
        elif not negative and actual:
            passed, category = False, "false_positive"
        else:
            passed, category = True, None
        result = {
            "case_path": str(case.get_case_path()),
            "case_type": "negative" if negative else "positive",
            "expected_diagnostics": expected,
            "actual_diagnostics": actual,
            "returncode": rc,
            "stdout": stdout,
            "stderr": stderr,
            "success": passed,
            "failure_category": category,
        }
        case.last_result = result
        return result

    def first_checker_generation(self):
        self.first_dir.mkdir(parents=True, exist_ok=True)
        self.debug_prompt_dir.mkdir(parents=True, exist_ok=True)
        for case_number, case in enumerate(self._candidate_negatives(), 1):
            case_dir = self.first_dir / f"negative_case_{case_number}"
            self._write_text(case_dir / "selected_case.cpp", case.get_case_code())
            for round_number in range(1, self.max_round + 1):
                self.generation_attempts += 1
                round_dir = case_dir / f"round_{round_number}"
                logics = self.run_logic_for_negative_case(
                    self.rule.get_rule_description(), case.get_case_code(), round_dir)
                metaops, api_refs = self.retrieve_context(logics)
                self._write_json(round_dir / "logic.json", logics)
                self._write_json(round_dir / "retrieved_metaops.json", metaops)
                self._write_json(round_dir / "retrieved_api_refs.json", api_refs)
                prompt = build_first_checker_prompt(
                    self.rule.get_rule_description(), case.get_case_code(),
                    json.dumps(metaops, ensure_ascii=False),
                    json.dumps(api_refs, ensure_ascii=False), self.checker_name, self.frontend,
                    self.rule.get_diagnostic(), self.rule.get_rule_id(), self._template_source())
                answer = self._invoke(prompt, round_dir / "generation_prompt.md")
                cpp = parse_generated_source(answer)
                generation_source = "llm"
                if not cpp:
                    cpp = self._fallback_source()
                    generation_source = "deterministic_fallback"
                if not cpp:
                    continue
                workspace = round_dir / "workspace"
                generation_context = json.dumps({
                    "rule_name": self.rule.get_rule_name(),
                    "rule_description": self.rule.get_rule_description(),
                    "rule_id": self.rule.get_rule_id(),
                    "diagnostic": self.rule.get_diagnostic(),
                    "initial_case": case.get_case_code(),
                    "extracted_logic": logics,
                    "retrieved_metaops": metaops,
                    "retrieved_api_refs": api_refs,
                }, ensure_ascii=False)
                compiled, cpp, plugin, _, _, _ = self._compile_with_repairs(
                    cpp, workspace, (metaops, api_refs), round_dir, generation_context)
                if not compiled:
                    continue
                candidate = Checker_CSA(
                    checker_code=cpp, name=self.checker_name, frontend=self.frontend,
                    plugin_path=str(plugin), version=1, generation_kind="initial",
                    metadata={
                        "case": str(case.get_case_path()),
                        "round": round_number,
                        "generation_source": generation_source,
                    })
                verification = self._run_case(case, candidate)
                self._write_json(round_dir / "verify.output.json", verification)
                if not verification["success"]:
                    continue
                candidate.set_passed_cases([case])
                self.generated, self.initial_case = candidate, case
                self._write_text(self.first_dir / "generated_checker.cpp", cpp)
                self._write_json(self.first_dir / "selected_case.json", {
                    "path": str(case.get_case_path()), "round": round_number})
                self.termination_reason = "initial_checker_generated"
                return True, candidate
            case.skipped = True
            self.skipped.add(str(case.get_case_path()))
            self.skipped_Test_Cases.append(case)
        self.termination_reason = "initial_generation_failed"
        self._write_result([], initial_success=False, augmentation_started=False)
        return False, None

    def run_all_test_cases(self, checker=None, write_result=True, augmentation_started=False):
        checker = checker or self.generated
        if checker is None:
            return self._write_result([], initial_success=False,
                                      augmentation_started=augmentation_started)
        results = [self._run_case(case, checker) for case in self.cases
                   if str(case.get_case_path()) not in self.skipped or case is self.initial_case]
        checker.set_passed_cases([
            case for case in self.cases
            if case.last_result and case.last_result["success"]
        ])
        if checker is self.generated:
            self.last_results = results
        return self._write_result(results, augmentation_started=augmentation_started) if write_result else results

    # Compatibility with the CodeQL generator's public spelling.
    def runAllTestCases(self, init_checker=None):
        result = self.run_all_test_cases(init_checker)
        return result["all_cases_success"], result["failed_case_list"], result["success_case_list"]

    def _augment_candidate(self, failed_result, current, attempt_dir):
        if not self.llm:
            return None
        case = next(case for case in self.cases
                    if str(case.get_case_path()) == failed_result["case_path"])
        kind = "negative" if failed_result["failure_category"] == "false_negative" else "positive"
        passed_code = "\n\n".join(item.get_case_code() for item in current.get_passed_cases())
        logic_prompt = build_augmentation_logic_prompt(
            kind, current.checker_code, passed_code, case.get_case_code(),
            json.dumps(failed_result, ensure_ascii=False))
        logic_answer = self._invoke(logic_prompt, attempt_dir / f"augmentation_logic_{kind}.md")
        try:
            logic = json.loads(re.sub(r"```json|```", "", logic_answer, flags=re.I).strip())
        except (json.JSONDecodeError, TypeError):
            logic = [{"intent": f"repair false {kind}", "case": str(case.get_case_path())}]
        context = self.retrieve_context(logic)
        prompt = build_augmentation_prompt(
            kind, self.rule.get_rule_description(), current.checker_code,
            json.dumps(logic, ensure_ascii=False),
            json.dumps({"metaops": context[0], "apis": context[1]}, ensure_ascii=False),
            passed_code, case.get_case_code(), json.dumps(failed_result, ensure_ascii=False))
        answer = self._invoke(prompt, attempt_dir / f"augmentation_check_{kind}.md")
        cpp = parse_generated_source(answer)
        if not cpp:
            return None
        workspace = attempt_dir / "workspace"
        generation_context = json.dumps({
            "rule_name": self.rule.get_rule_name(),
            "rule_description": self.rule.get_rule_description(),
            "rule_id": self.rule.get_rule_id(),
            "diagnostic": self.rule.get_diagnostic(),
            "failed_check_result": failed_result,
            "failed_case": case.get_case_code(),
            "augmentation_logic": logic,
            "retrieved_metaops": context[0],
            "retrieved_api_refs": context[1],
        }, ensure_ascii=False)
        compiled, cpp, plugin, _, _, _ = self._compile_with_repairs(
            cpp, workspace, context, attempt_dir, generation_context)
        if not compiled:
            return None
        return Checker_CSA(
            checker_code=cpp, name=self.checker_name, frontend=self.frontend,
            plugin_path=str(plugin), version=current.version + 1,
            generation_kind=f"augmentation_{kind}",
            metadata={"target_case": str(case.get_case_path())})

    def checker_augmentation(self, init_checker=None):
        current = init_checker or self.generated
        if current is None:
            return None
        baseline = self.run_all_test_cases(current, write_result=False, augmentation_started=True)
        failed = [item for item in baseline if not item["success"]]
        if not failed:
            self.generated = current
            self.termination_reason = "all_cases_passed"
            self._write_result(baseline, augmentation_started=True)
            return current
        seen_failures = set()
        for attempt in range(1, self.max_augmentation_tries + 1):
            semantic_failures = [item for item in failed
                                 if item["failure_category"] in {"false_negative", "false_positive"}
                                 and item["case_path"] not in seen_failures]
            if not semantic_failures:
                self.termination_reason = "no_progress_or_execution_failures"
                break
            target = semantic_failures[0]
            seen_failures.add(target["case_path"])
            self.augmentation_attempts += 1
            attempt_dir = self.rule_dir / "augmentation" / f"attempt_{attempt}"
            candidate = self._augment_candidate(target, current, attempt_dir)
            if candidate is None:
                continue
            targeted = self._run_case(
                next(case for case in self.cases if str(case.get_case_path()) == target["case_path"]),
                candidate)
            self._write_json(attempt_dir / "target_verify.json", targeted)
            if not targeted["success"]:
                continue
            candidate_results = self.run_all_test_cases(candidate, write_result=False, augmentation_started=True)
            old_score = sum(item["success"] for item in baseline)
            new_score = sum(item["success"] for item in candidate_results)
            self._write_json(attempt_dir / "regression_result.json", candidate_results)
            old_passed = {item["case_path"] for item in baseline if item["success"]}
            new_passed = {item["case_path"] for item in candidate_results if item["success"]}
            if new_score < old_score or not old_passed.issubset(new_passed):
                continue
            current, baseline = candidate, candidate_results
            failed = [item for item in baseline if not item["success"]]
            current.set_passed_cases([
                case for case in self.cases
                if any(item["case_path"] == str(case.get_case_path()) and item["success"]
                       for item in baseline)
            ])
            self.generated = current
            self.rule.add_checker(current)
            snapshot_dir = self.rule_dir / "checker_versions" / f"version_{current.version}"
            self._write_text(snapshot_dir / f"{self.checker_name}.cpp", current.checker_code)
            seen_failures.clear()
            if not failed:
                self.termination_reason = "all_cases_passed"
                break
        else:
            self.termination_reason = "max_augmentation_tries_reached"
        self.generated = current
        self.last_results = baseline
        self._write_result(baseline, augmentation_started=True)
        return current

    def _write_result(self, results, initial_success=None, augmentation_started=False):
        successes = [item for item in results if item.get("success")]
        failures = [item for item in results if not item.get("success")]
        negatives = [case for case in self.cases if is_negative(case)]
        positives = [case for case in self.cases if not is_negative(case)]
        initial_success = bool(self.generated) if initial_success is None else initial_success
        result = {
            "stage": "full_lifecycle" if augmentation_started else "A+B",
            "rule": self.rule.get_rule_name(),
            "rule_id": self.rule.get_rule_id(),
            "checker": self.checker_name,
            "frontend": self.frontend,
            "initial_case": str(self.initial_case.get_case_path()) if self.initial_case else None,
            "negative_case_amount": len(negatives),
            "positive_case_amount": len(positives),
            "success_case_list": successes,
            "failed_case_list": failures,
            "performance": f"{len(successes)}/{len(results)}",
            "compile_success": bool(self.generated),
            "initial_case_success": initial_success,
            "all_cases_success": bool(results) and not failures,
            "augmentation_started": augmentation_started,
            "generation_attempts": self.generation_attempts,
            "compile_attempts": self.compile_attempts,
            "augmentation_attempts": self.augmentation_attempts,
            "skipped_cases": sorted(self.skipped),
            "termination_reason": self.termination_reason,
            "checker_versions": [checker.snapshot() for checker in self.rule.get_checkers()],
            "total_cost": self.total_cost,
            "cost_note": "not calculated: model pricing is not configured",
            "token_usage": self.token_usage,
            "llm_model": getattr(self.llm, "model", None),
            "retrieval": self.retrieval_stats,
            "initial_generation_source": (
                self.rule.get_checkers()[0].metadata.get("generation_source")
                if self.rule.get_checkers() else
                (self.generated.metadata.get("generation_source") if self.generated else None)
            ),
            "llm_failure_amount": len(self.llm_failures),
            "llm_failures": self.llm_failures,
        }
        self._write_json(self.rule_dir / "checker_generation_result.json", result)
        return result

    def generate_checker(self):
        success, checker = self.first_checker_generation()
        if not success:
            return None
        self.rule.add_checker(checker)
        self.skipped.clear()
        for case in self.cases:
            case.skipped = False
        self.checker_augmentation(checker)
        return self.rule.get_checkers()
