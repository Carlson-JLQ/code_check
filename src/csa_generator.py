"""CodeQL-shaped generation lifecycle for standalone CSA checker plugins."""

import json
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
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


def parse_json_payload(answer: str, default=None):
    """Read a JSON value out of an LLM answer that may carry prose or fences.

    Mirrors csa_official_checker_logic_extract/decompose_with_llm.py
    parse_json_response, kept local so the CSA source tree stays importable
    without sys.path surgery. Keep the two in sync.
    """
    text = re.sub(r"```json|```", "", answer or "", flags=re.I).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Models routinely prepend a sentence to the payload. Slice from the first
    # opening bracket to its matching close, ignoring brackets inside strings.
    for opening, closing in (("[", "]"), ("{", "}")):
        start = text.find(opening)
        if start < 0:
            continue
        depth, in_string, escaped = 0, False, False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == opening:
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:index + 1])
                    except json.JSONDecodeError:
                        break
    return default


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

  // CompoundStmt::children() yields DeclStmt nodes as well as Expr nodes.
  // Recursing over every Stmt child is what makes the initializer of
  // `int r = f() + g();` reachable; a worklist filtered to Expr never sees it.
  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC,
                   BugReporter &BR) const {{
    if (!S)
      return;
    // Replace this with the rule's violation test, then call
    // emitASTReport(S, ADC, BR) on the most specific violating node.
    for (const Stmt *Child : S->children())
      inspectStmt(Child, ADC, BR);
  }}

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {{
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;
    inspectStmt(ADC->getBody(), ADC, BR);
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
        max_compiler_trys=4,
        max_round=3,
        max_initial_negative_cases=3,
        max_augmentation_tries=16,
        max_semantic_repair_tries=3,
        max_technical_retries_per_case=2,
        max_execution_repair_tries=2,
        max_rule_seconds=2400,
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
        jobs=1,
        use_deterministic_fallback=True,
        promote_with_execution_failures=True,
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
        self.max_initial_negative_cases = max(1, int(max_initial_negative_cases))
        self.max_augmentation_tries = max(0, int(max_augmentation_tries))
        self.max_semantic_repair_tries = max(1, int(max_semantic_repair_tries))
        self.max_technical_retries_per_case = max(0, int(max_technical_retries_per_case))
        self.max_execution_repair_tries = max(0, int(max_execution_repair_tries))
        self.max_rule_seconds = max(0, int(max_rule_seconds or 0))
        self.max_llm_tries = max(1, int(max_llm_tries))
        self.jobs = max(1, int(jobs))
        self.use_deterministic_fallback = bool(use_deterministic_fallback)
        self.promote_with_execution_failures = bool(promote_with_execution_failures)
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
        self.baseline_checker: Optional[Checker_CSA] = None
        self.baseline_results = []
        self.augmentation_history = []
        self.rollback_count = 0
        self.accepted_augmentation_amount = 0
        self.rejected_augmentation_amount = 0
        self.final_checker_source = None
        self.initial_candidate_results = []
        self.initial_attempted_case = None
        self.initial_compile_success = False
        self.logic_parse_failures = []
        # Highest-scoring candidate ever produced, retained even when the
        # acceptance gate rejects it. A 19/20 candidate was previously deleted
        # in favour of the 18/20 that happened to pass the gate.
        self.best_candidate: Optional[Checker_CSA] = None
        self.best_results = []
        self.best_score = None
        self.best_rank = None
        self.best_source_path = None
        self.best_plugin_path = None
        self.promoted_from_best = False
        self.started_at = None

    def get_total_cost(self):
        return self.total_cost

    def select_initial_case(self):
        return next((case for case in self.cases if not case.skipped
                     and str(case.get_case_path()) not in self.skipped
                     and is_negative(case)), None)

    def _candidate_negatives(self):
        candidates = [case for case in self.cases if is_negative(case) and not case.skipped
                      and str(case.get_case_path()) not in self.skipped]
        return candidates[:self.max_initial_negative_cases]

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
        value = parse_json_payload(answer)
        if value is not None:
            return value if isinstance(value, list) else [value]
        self.logic_parse_failures.append(str(artifact_dir) if artifact_dir else "<unknown>")
        # Never name a concrete callback here. A hardcoded check::ASTCodeBody
        # turned every logic-extraction failure into a wrong-callback checker.
        return [{
            "intent": f"implement the rule: {rule_description}",
            "trigger": "unknown - choose the callback from the rule shape",
            "traversal": "unknown - derive it from the negative test",
            "constraints": ["inspect the complete AST", "emit the configured diagnostic"],
            "api_search_terms": ["ASTCodeBody", "ASTDecl", "Stmt", "Decl", "BugType", "CheckerRegistry"],
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
        if not self.use_deterministic_fallback:
            return ""
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
            if self.initial_attempted_case is None:
                self.initial_attempted_case = case
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
                    json.dumps(logics, ensure_ascii=False),
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
                    self.initial_candidate_results.append({
                        "case_path": str(case.get_case_path()),
                        "case_type": "negative",
                        "expected_diagnostics": expected_diagnostics(case.get_case_code()),
                        "actual_diagnostics": [], "returncode": None, "stdout": "", "stderr": "",
                        "success": False, "failure_category": "generation_failure",
                        "candidate_number": case_number, "round": round_number,
                    })
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
                compiled, cpp, plugin, compile_rc, compile_stdout, compile_stderr = self._compile_with_repairs(
                    cpp, workspace, (metaops, api_refs), round_dir, generation_context)
                self.initial_compile_success |= compiled
                if not compiled:
                    self.initial_candidate_results.append({
                        "case_path": str(case.get_case_path()),
                        "case_type": "negative",
                        "expected_diagnostics": expected_diagnostics(case.get_case_code()),
                        "actual_diagnostics": [], "returncode": compile_rc,
                        "stdout": compile_stdout, "stderr": compile_stderr,
                        "success": False, "failure_category": "compile_failure",
                        "candidate_number": case_number, "round": round_number,
                    })
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
                verification.update({"candidate_number": case_number, "round": round_number})
                self.initial_candidate_results.append(verification)
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
        self._write_result(self.initial_candidate_results, initial_success=False,
                           augmentation_started=False)
        return False, None

    def run_all_test_cases(self, checker=None, write_result=True, augmentation_started=False):
        checker = checker or self.generated
        if checker is None:
            return self._write_result([], initial_success=False,
                                      augmentation_started=augmentation_started)
        selected = [case for case in self.cases
                    if str(case.get_case_path()) not in self.skipped or case is self.initial_case]
        if self.jobs > 1 and len(selected) > 1:
            # Each _run_case is an isolated clang subprocess. Reassemble in the
            # original case order so results stay deterministic.
            with ThreadPoolExecutor(max_workers=self.jobs) as pool:
                results = list(pool.map(lambda case: self._run_case(case, checker), selected))
        else:
            results = [self._run_case(case, checker) for case in selected]
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

    def _identity_gaps(self, cpp):
        required = [
            self.checker_name,
            f'"{self.frontend}"',
            "clang_registerCheckers",
            "clang_analyzerAPIVersionString",
        ]
        return [item for item in required if item not in cpp]

    def _checker_identity_valid(self, cpp):
        return not self._identity_gaps(cpp)

    @staticmethod
    def _failure_kind(failure_category):
        return {
            "false_negative": "negative",
            "false_positive": "positive",
        }.get(failure_category, "execution")

    def _sibling_failure_digest(self, failed_result, all_failures, limit=6):
        """Other failures of the same category, so a fix cannot special-case one.

        Two augmentation attempts previously "fixed" all ten false positives by
        disabling the report path, flipping ten negatives to false negatives,
        because the prompt only ever showed one case.
        """
        siblings = [item for item in (all_failures or [])
                    if item.get("failure_category") == failed_result.get("failure_category")
                    and item.get("case_path") != failed_result.get("case_path")]
        if not siblings:
            return "(none)"
        digest = []
        for item in siblings[:limit]:
            case = next((case for case in self.cases
                         if str(case.get_case_path()) == item["case_path"]), None)
            digest.append({
                "case_path": item["case_path"],
                "case_type": item.get("case_type"),
                "expected_diagnostics": item.get("expected_diagnostics"),
                "actual_diagnostics": item.get("actual_diagnostics"),
                "case_code": case.get_case_code() if case else "",
            })
        text = json.dumps(digest, ensure_ascii=False, indent=2)
        if len(siblings) > limit:
            text += f"\n\n({len(siblings) - limit} further cases fail the same way.)"
        return text

    def _augment_candidate(self, failed_result, current, attempt_dir,
                           failure_history=None, semantic_attempt=1,
                           all_failures=None, all_attempts=None):
        self._last_augmentation_build = {"reason": None, "detail": None}
        if not self.llm:
            self._last_augmentation_build["reason"] = "llm_unavailable"
            return None
        case = next(case for case in self.cases
                    if str(case.get_case_path()) == failed_result["case_path"])
        kind = self._failure_kind(failed_result["failure_category"])
        passed_code = "\n\n".join(item.get_case_code() for item in current.get_passed_cases())
        history_json = json.dumps(failure_history or [], ensure_ascii=False)
        attempts_json = json.dumps(all_attempts or [], ensure_ascii=False)
        siblings = self._sibling_failure_digest(failed_result, all_failures)
        logic_prompt = build_augmentation_logic_prompt(
            kind, current.checker_code, passed_code, case.get_case_code(),
            json.dumps(failed_result, ensure_ascii=False), history_json,
            siblings, attempts_json)
        logic_answer = self._invoke(logic_prompt, attempt_dir / "semantic_analysis_prompt.md")
        logic = parse_json_payload(logic_answer)
        if not isinstance(logic, dict):
            logic = {
                "root_cause": f"unparsed false {kind} analysis",
                "semantic_change": "repair the target without changing passed behavior",
                "api_search_terms": [],
            }
        context = self.retrieve_context(logic)
        prompt = build_augmentation_prompt(
            kind, self.rule.get_rule_description(), current.checker_code,
            json.dumps(logic, ensure_ascii=False),
            json.dumps({"metaops": context[0], "apis": context[1]}, ensure_ascii=False),
            passed_code, case.get_case_code(), json.dumps(failed_result, ensure_ascii=False),
            history_json, self.checker_name, self.frontend,
            self.rule.get_rule_id(), self.rule.get_diagnostic(),
            siblings, attempts_json)
        answer = self._invoke(prompt, attempt_dir / "augmentation_prompt.md")
        cpp = parse_generated_source(answer)
        if not cpp:
            self._last_augmentation_build["reason"] = "invalid_llm_output"
            return None
        self._write_text(attempt_dir / "generated_checker.cpp", cpp)
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
            "previous_rejected_attempts": failure_history or [],
            "semantic_attempt": semantic_attempt,
        }, ensure_ascii=False)
        compiled, cpp, plugin, _, _, _ = self._compile_with_repairs(
            cpp, workspace, context, attempt_dir, generation_context)
        if not compiled:
            self._last_augmentation_build["reason"] = "compile_failed"
            return None
        self._write_text(attempt_dir / "generated_checker.cpp", cpp)
        gaps = self._identity_gaps(cpp)
        if gaps:
            self._last_augmentation_build["reason"] = "checker_identity_changed"
            self._last_augmentation_build["detail"] = {"missing_tokens": gaps}
            if plugin.exists():
                plugin.unlink()
            return None
        return Checker_CSA(
            checker_code=cpp, name=self.checker_name, frontend=self.frontend,
            plugin_path=str(plugin), version=current.version + 1,
            generation_kind=f"augmentation_{kind}",
            metadata={
                "target_case": str(case.get_case_path()),
                "semantic_attempt": semantic_attempt,
            })

    def _record_rejected_candidate(self, attempt_dir, manifest, reason,
                                   target_result=None, regression=None, candidate=None,
                                   gate_violations=None, detail=None):
        manifest.update({
            "status": "rejected",
            "rejection_reason": reason,
            "gate_violations": gate_violations or [],
            "rejection_detail": detail,
            "target_success": bool(target_result and target_result.get("success")),
        })
        if regression is not None:
            manifest["new_score"] = sum(item.get("success", False) for item in regression)
        self.rejected_augmentation_amount += 1
        self.rollback_count += 1
        self.augmentation_history.append(dict(manifest))
        self._write_json(attempt_dir / "candidate_manifest.json", manifest)
        self._write_json(attempt_dir / "rejection_reason.json", {
            "reason": reason,
            "gate_violations": gate_violations or [],
            "rejection_detail": detail,
            "base_version_retained": manifest["base_version"],
        })
        if candidate:
            # Never delete the retained best candidate's artifact.
            if candidate is self.best_candidate:
                return
            plugin = Path(candidate.plugin_path)
            try:
                plugin.resolve().relative_to(Path(attempt_dir).resolve())
                is_attempt_artifact = True
            except ValueError:
                is_attempt_artifact = False
            if is_attempt_artifact and plugin.exists():
                plugin.unlink()

    def _persist_candidate(self, candidate, results, version_dir):
        version_dir = Path(version_dir)
        source_path = version_dir / "checker.cpp"
        self._write_text(source_path, candidate.checker_code)
        self._write_json(version_dir / "regression_result.json", results)
        plugin = Path(candidate.plugin_path)
        stored_plugin = candidate.plugin_path
        if plugin.exists():
            copied = version_dir / "plugin.so"
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(plugin, copied)
            stored_plugin = str(copied)
        return str(source_path), stored_plugin

    @staticmethod
    def _candidate_rank(results):
        """Order candidates by score, breaking ties on fewer analyzer crashes."""
        score = sum(bool(item.get("success")) for item in results)
        crashes = sum(1 for item in results
                      if item.get("failure_category") == "execution_failure")
        return (score, -crashes)

    def _record_best_candidate(self, candidate, results):
        """Retain the highest-ranked candidate regardless of the accept gate.

        The gate is a monotonicity contract for what becomes the next baseline,
        not a reason to destroy a better checker. A 19/20 candidate with no
        regressions was previously deleted in favour of an 18/20.
        """
        rank = self._candidate_rank(results)
        if self.best_rank is not None and rank <= self.best_rank:
            return False
        self.best_rank = rank
        self.best_score = rank[0]
        self.best_candidate = candidate
        self.best_results = list(results)
        self.best_source_path, self.best_plugin_path = self._persist_candidate(
            candidate, results, self.rule_dir / "augmentation" / "best_candidate")
        return True

    def _rule_time_exhausted(self):
        if not self.max_rule_seconds or self.started_at is None:
            return False
        return (time.monotonic() - self.started_at) >= self.max_rule_seconds

    def _save_accepted_candidate(self, candidate, results, attempt_dir, manifest):
        version_dir = self.rule_dir / "augmentation" / "accepted_versions" / f"version_{candidate.version}"
        source_path, accepted_plugin = self._persist_candidate(candidate, results, version_dir)
        candidate.plugin_path = accepted_plugin
        manifest.update({
            "status": "accepted",
            "rejection_reason": None,
            "gate_violations": [],
            "target_success": True,
            "new_score": sum(item.get("success", False) for item in results),
            "accepted_source": source_path,
            "accepted_plugin": candidate.plugin_path,
        })
        self.accepted_augmentation_amount += 1
        self.augmentation_history.append(dict(manifest))
        self._write_json(attempt_dir / "candidate_manifest.json", manifest)
        self.final_checker_source = source_path

    @staticmethod
    def _gate_violations(baseline, candidate_results):
        """Name the clause that fired, not just that something did.

        The model was previously told only "full_regression_failed" alongside
        numbers that read as a pass, and responded by weakening the checker.
        """
        def paths(results, category=None):
            if category is None:
                return {item["case_path"] for item in results if item["success"]}
            return {item["case_path"] for item in results
                    if item["failure_category"] == category}

        old_score = sum(item["success"] for item in baseline)
        new_score = sum(item["success"] for item in candidate_results)
        violations = []
        if new_score <= old_score:
            violations.append(
                f"score did not improve: {new_score} passing vs {old_score} before")
        regressed = sorted(paths(baseline) - paths(candidate_results))
        if regressed:
            violations.append(
                "regressed previously passing cases: " + ", ".join(regressed))
        for category, label in (
            ("execution_failure", "made the analyzer crash or exit non-zero on"),
            ("false_positive", "introduced new false positives on"),
            ("false_negative", "introduced new false negatives on"),
        ):
            introduced = sorted(paths(candidate_results, category) - paths(baseline, category))
            if introduced:
                violations.append(f"{label}: " + ", ".join(introduced))
        return violations, old_score, new_score

    def checker_augmentation(self, init_checker=None):
        current = init_checker or self.generated
        if current is None:
            return None
        if self.started_at is None:
            self.started_at = time.monotonic()
        self.baseline_checker = current
        baseline = self.run_all_test_cases(current, write_result=False, augmentation_started=True)
        self.baseline_results = list(baseline)
        baseline_dir = self.rule_dir / "augmentation" / "baseline"
        self._write_text(baseline_dir / "checker.cpp", current.checker_code)
        self._write_json(baseline_dir / "regression_result.json", baseline)
        self.final_checker_source = str(self.first_dir / "generated_checker.cpp")
        self._record_best_candidate(current, baseline)
        failed = [item for item in baseline if not item["success"]]
        if not failed:
            self.generated = current
            self.last_results = baseline
            self.termination_reason = "all_cases_passed"
            self._write_result(baseline, augmentation_started=True)
            return current
        # Semantic and technical budgets are separate. A candidate that failed
        # to compile says nothing about whether the case is repairable, and
        # charging it against the semantic budget stranded unused attempts.
        target_attempts = {}
        technical_attempts = {}
        failure_history = {}
        all_attempts = []
        priority = {"false_negative": 0, "false_positive": 1, "execution_failure": 2}
        attempt = 0
        self.termination_reason = "max_augmentation_tries_reached"
        while attempt < self.max_augmentation_tries:
            if self._rule_time_exhausted():
                self.termination_reason = "rule_time_budget_reached"
                break
            repairable = sorted(
                (item for item in failed
                 if item["failure_category"] in priority
                 and target_attempts.get(item["case_path"], 0) < self.max_semantic_repair_tries
                 and technical_attempts.get(item["case_path"], 0) < self.max_technical_retries_per_case),
                key=lambda item: (priority[item["failure_category"]], item["case_path"]),
            )
            if not repairable:
                self.termination_reason = "semantic_repair_limit_reached"
                break
            attempt += 1
            target = repairable[0]
            target_path = target["case_path"]
            semantic_attempt = target_attempts.get(target_path, 0) + 1
            self.augmentation_attempts += 1
            attempt_dir = self.rule_dir / "augmentation" / f"attempt_{attempt}"
            manifest = {
                "base_version": current.version,
                "candidate_version": current.version + 1,
                "target_case": target_path,
                "failure_category": target["failure_category"],
                "status": "pending",
                "rejection_reason": None,
                "compile_attempts_before": self.compile_attempts,
                "semantic_attempt": semantic_attempt,
                "old_score": sum(item["success"] for item in baseline),
            }
            self._write_json(attempt_dir / "candidate_manifest.json", manifest)
            candidate = self._augment_candidate(
                target, current, attempt_dir,
                failure_history.get(target_path, []), semantic_attempt,
                all_failures=failed, all_attempts=all_attempts)
            manifest["compile_attempts"] = self.compile_attempts - manifest.pop("compile_attempts_before")
            build = getattr(self, "_last_augmentation_build", {}) or {}
            if candidate is None:
                reason = build.get("reason") or "candidate_generation_failed"
                detail = build.get("detail")
                technical_attempts[target_path] = technical_attempts.get(target_path, 0) + 1
                self._record_rejected_candidate(attempt_dir, manifest, reason, detail=detail)
                entry = {
                    "target_case": target_path,
                    "semantic_attempt": semantic_attempt,
                    "reason": reason,
                    "detail": detail,
                }
                failure_history.setdefault(target_path, []).append(entry)
                all_attempts.append(entry)
                continue
            # A candidate that built is a semantic outcome from here on.
            target_attempts[target_path] = target_attempts.get(target_path, 0) + 1
            targeted = self._run_case(
                next(case for case in self.cases if str(case.get_case_path()) == target_path),
                candidate)
            self._write_json(attempt_dir / "target_verify.json", targeted)
            if not targeted["success"]:
                self._record_rejected_candidate(
                    attempt_dir, manifest, "target_verification_failed", targeted, candidate=candidate)
                entry = {
                    "target_case": target_path,
                    "semantic_attempt": semantic_attempt,
                    "reason": "target_verification_failed",
                    "detail": "the candidate still does not resolve the target case",
                    "result": targeted,
                }
                failure_history.setdefault(target_path, []).append(entry)
                all_attempts.append(entry)
                continue
            candidate_results = self.run_all_test_cases(candidate, write_result=False, augmentation_started=True)
            self._write_json(attempt_dir / "regression_result.json", candidate_results)
            # Retain before any rejection path can delete the artifact.
            self._record_best_candidate(candidate, candidate_results)
            gate_violations, old_score, new_score = self._gate_violations(baseline, candidate_results)
            if gate_violations:
                self._record_rejected_candidate(
                    attempt_dir, manifest, "full_regression_failed", targeted,
                    candidate_results, candidate, gate_violations=gate_violations)
                entry = {
                    "target_case": target_path,
                    "semantic_attempt": semantic_attempt,
                    "reason": "full_regression_failed",
                    "gate_violations": gate_violations,
                    "old_score": old_score,
                    "new_score": new_score,
                }
                failure_history.setdefault(target_path, []).append(entry)
                all_attempts.append(entry)
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
            self._save_accepted_candidate(current, baseline, attempt_dir, manifest)
            all_attempts.append({
                "target_case": target_path,
                "semantic_attempt": semantic_attempt,
                "reason": "accepted",
                "old_score": old_score,
                "new_score": new_score,
            })
            snapshot_dir = self.rule_dir / "checker_versions" / f"version_{current.version}"
            self._write_text(snapshot_dir / f"{self.checker_name}.cpp", current.checker_code)
            if not failed:
                self.termination_reason = "all_cases_passed"
                break
        self.generated = current
        self.last_results = baseline
        self._repair_best_candidate_crashes()
        final_results = self._promote_best_candidate(baseline)
        self._write_result(final_results, augmentation_started=True)
        return self.generated

    def _repair_best_candidate_crashes(self):
        """Spend a dedicated budget turning the best candidate's crashes into passes.

        An analyzer assertion is a defect in the generated checker, not a
        property of the test case, and it is what kept the highest-scoring
        candidate out of the accepted lineage.
        """
        if not self.max_execution_repair_tries or self.best_candidate is None or not self.llm:
            return
        for index in range(1, self.max_execution_repair_tries + 1):
            crashes = [item for item in self.best_results
                       if item.get("failure_category") == "execution_failure"]
            if not crashes or self._rule_time_exhausted():
                return
            attempt_dir = self.rule_dir / "augmentation" / f"execution_repair_{index}"
            base = self.best_candidate
            self.augmentation_attempts += 1
            candidate = self._augment_candidate(
                crashes[0], base, attempt_dir, failure_history=[], semantic_attempt=index,
                all_failures=[item for item in self.best_results if not item["success"]],
                all_attempts=self.augmentation_history)
            build = getattr(self, "_last_augmentation_build", {}) or {}
            if candidate is None:
                self._write_json(attempt_dir / "rejection_reason.json", {
                    "phase": "execution_repair",
                    "reason": build.get("reason") or "candidate_generation_failed",
                    "rejection_detail": build.get("detail"),
                })
                continue
            results = self.run_all_test_cases(candidate, write_result=False, augmentation_started=True)
            self._write_json(attempt_dir / "regression_result.json", results)
            promoted = self._record_best_candidate(candidate, results)
            remaining = sum(1 for item in results
                            if item.get("failure_category") == "execution_failure")
            self._write_json(attempt_dir / "candidate_manifest.json", {
                "phase": "execution_repair",
                "attempt": index,
                "base_version": base.version,
                "target_case": crashes[0]["case_path"],
                "new_score": sum(bool(item.get("success")) for item in results),
                "execution_failures": remaining,
                "promoted_to_best": promoted,
            })
            if promoted and not remaining:
                return

    def _promote_best_candidate(self, final_results):
        """Ship the best checker produced, not merely the last one accepted."""
        if self.best_candidate is None or self.best_candidate is self.generated:
            return final_results
        if self._candidate_rank(self.best_results) <= self._candidate_rank(final_results):
            return final_results
        crashes = sum(1 for item in self.best_results
                      if item.get("failure_category") == "execution_failure")
        if crashes and not self.promote_with_execution_failures:
            return final_results
        checker = self.best_candidate
        if self.best_plugin_path:
            checker.plugin_path = self.best_plugin_path
        checker.set_passed_cases([
            case for case in self.cases
            if any(item["case_path"] == str(case.get_case_path()) and item["success"]
                   for item in self.best_results)
        ])
        self.generated = checker
        self.rule.add_checker(checker)
        self.final_checker_source = self.best_source_path
        self.promoted_from_best = True
        self.last_results = list(self.best_results)
        return list(self.best_results)

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
            "initial_attempted_case": (
                str(self.initial_attempted_case.get_case_path())
                if self.initial_attempted_case else None
            ),
            "initial_candidate_amount": len(self.initial_candidate_results),
            "initial_candidate_result_list": self.initial_candidate_results,
            "negative_case_amount": len(negatives),
            "positive_case_amount": len(positives),
            "success_case_list": successes,
            "failed_case_list": failures,
            "performance": f"{len(successes)}/{len(results)}",
            "compile_success": bool(self.generated),
            "initial_compile_success": self.initial_compile_success,
            "initial_case_success": initial_success,
            "all_cases_success": bool(results) and not failures,
            "augmentation_started": augmentation_started,
            "generation_attempts": self.generation_attempts,
            "compile_attempts": self.compile_attempts,
            "augmentation_attempts": self.augmentation_attempts,
            "baseline_version": self.baseline_checker.version if self.baseline_checker else None,
            "active_version": self.generated.version if self.generated else None,
            "best_version": self.best_candidate.version if self.best_candidate else (
                self.generated.version if self.generated else None),
            "best_score": self.best_score,
            "best_checker_source": self.best_source_path,
            "best_plugin_path": self.best_plugin_path,
            "promoted_from_best": self.promoted_from_best,
            "final_execution_failure_amount": sum(
                1 for item in failures
                if item.get("failure_category") == "execution_failure"
            ),
            "logic_parse_failure_amount": len(self.logic_parse_failures),
            "logic_parse_failures": self.logic_parse_failures,
            "rollback_performed": self.rollback_count > 0,
            "rollback_count": self.rollback_count,
            "accepted_augmentation_amount": self.accepted_augmentation_amount,
            "rejected_augmentation_amount": self.rejected_augmentation_amount,
            "augmentation_history": self.augmentation_history,
            "remaining_semantic_failures": [
                item for item in failures
                if item.get("failure_category") in {"false_negative", "false_positive"}
            ],
            "final_checker_source": self.final_checker_source,
            "final_plugin_path": self.generated.plugin_path if self.generated else None,
            "skipped_cases": sorted(self.skipped),
            "termination_reason": self.termination_reason,
            "run_status": (
                "success" if results and not failures else
                "partial" if results else "failed"
            ),
            "failure_reason": self.termination_reason if failures or not results else None,
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
        if self.started_at is None:
            self.started_at = time.monotonic()
        success, checker = self.first_checker_generation()
        if not success:
            return None
        self.rule.add_checker(checker)
        self.skipped.clear()
        for case in self.cases:
            case.skipped = False
        self.checker_augmentation(checker)
        return self.rule.get_checkers()
