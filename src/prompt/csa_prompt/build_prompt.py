"""Prompt builders for the CodeQL-shaped CSA generation lifecycle."""


# Facts the model cannot recover from the retrieved context. Every one of these
# corresponds to a measured failure mode in the first GJB8114 batch: six
# candidates casting the check::ASTCodeBody argument to RecordDecl (dead code,
# zero reports) and three seeding a worklist from Expr children only (the
# violation lived in a DeclStmt initializer).
CALLBACK_FACTS = """## Clang Static Analyzer callback facts

Read this before choosing a callback. These are hard constraints of the
framework, not style advice.

- `check::ASTCodeBody` fires ONLY for Decls that have a body: FunctionDecl,
  ObjCMethodDecl, BlockDecl. `AnalysisConsumer::HandleCode` begins with
  `if (!D->hasBody()) return;`. Writing `dyn_cast<RecordDecl>(D)` or
  `dyn_cast<TagDecl>(D)` inside `checkASTCodeBody` produces dead code that
  reports nothing at all.
- If the rule is about a declaration itself (record, field, enum, typedef,
  global variable, function signature), use `check::ASTDecl<RecordDecl>` with
  the matching Decl subclass and inspect the Decl argument directly.
- If the rule needs whole-translation-unit or cross-declaration reasoning
  (shadowing a global, declaration ordering, "anywhere in this file"), use
  `check::ASTDecl<TranslationUnitDecl>` and walk `TU->decls()` yourself, or
  reach the enclosing context from a code body through
  `AM.getAnalysisDeclContext(D)->getDecl()->getDeclContext()`.
- `CompoundStmt::children()` yields `DeclStmt` nodes, not only `Expr` nodes.
  `int r = f() + g();` is a `DeclStmt` and its initializer is invisible to a
  worklist filtered to `Expr`. Recurse over every `Stmt` child, or use
  `RecursiveASTVisitor`.
- Call `IgnoreParenImpCasts()` on operands before matching them.
- `check::ASTCodeBody` and `check::ASTDecl<T>` are path-insensitive. Report with
  `BasicBugReport` and `PathDiagnosticLocation`. Never construct a
  `PathSensitiveBugReport` and never fabricate or pass a null `ExplodedNode`
  from these callbacks.
"""


def build_logic_prompt(rule_description, test_code):
    return f"""Extract a JSON list of detection logic units for a Clang Static Analyzer checker.
Rule: {rule_description}
Negative test:
{test_code}
{CALLBACK_FACTS}
Each unit must contain these keys:
- intent: what this unit detects
- trigger: the CSA callback this unit runs in, chosen using the facts above
- traversal: how the unit reaches the violating node from the callback argument
- constraints: the conditions that make a node a violation
- api_search_terms: clang / CSA API names this unit needs

Return JSON only. Start your answer with `[`. Do not write any prose before or
after the JSON.
"""


def build_first_checker_prompt(
    rule_description,
    test_code,
    logic,
    metaops,
    api_refs,
    checker_name="GeneratedNoAssignmentInConditionChecker",
    frontend="gjb8114.NoAssignmentInCondition",
    diagnostic="",
    rule_id="",
    template_cpp="",
):
    return f"""Generate a standalone Clang Static Analyzer dynamic checker plugin.
Implementation class: {checker_name}
Frontend: {frontend}
Rule: {rule_description}
Required diagnostic text: {diagnostic}
Rule identifier: {rule_id}

## Negative test the checker must report
{test_code}

## Extracted detection logic (your implementation plan)
{logic}

## Retrieved CSA MetaOps (logic units from official Clang checkers)
{metaops}

## Retrieved CSA APIs
{api_refs}

{CALLBACK_FACTS}
## Known compiling plugin template
```cpp
{template_cpp}
```

Implement the extracted detection logic rather than the placeholder walk in the
structural template. The template shows the include set, class placement,
BugType construction, report construction and registration exports; it does not
show the rule. If the extracted logic selects a callback other than
check::ASTCodeBody, change the Checker<> base accordingly.

Inspect nested syntax where the rule requires it and report the most specific
violating source location. Export clang_registerCheckers and
clang_analyzerAPIVersionString. Keep the entire plugin in this C++ file.
Prefer APIs from the retrieved context; if you need another clang AST API, use
only ones you are certain exist. Never invent member functions.
Do not edit Checkers.td or LLVM sources.
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate or include a project-local header.
"""


def build_compiler_analysis_prompt(cpp, compiler_output, api_refs, metaops,
                                   generation_context=""):
    return f"""Analyze this CSA plugin compiler failure and return JSON with
repair_steps and api_search_terms.
Compiler output:
{compiler_output}
Original generation context:
{generation_context}
Implementation:
{cpp}
Known APIs:
{api_refs}
Known MetaOps:
{metaops}

Return JSON only. Start your answer with `{{`. Do not write any prose before or
after the JSON.
"""


def build_compiler_repair_prompt(cpp, compiler_output, analysis, api_refs, metaops,
                                 generation_context="", template_cpp=""):
    return f"""Repair this standalone CSA plugin. Preserve its class and frontend names.
Compiler output:
{compiler_output}
Analysis:
{analysis}
Original generation context:
{generation_context}
Relevant APIs:
{api_refs}
Relevant MetaOps:
{metaops}
Current implementation:
{cpp}
Known compiling implementation template:
{template_cpp}
When uncertain, restore the template's include set, registration functions,
BugReport construction, and class placement.
For check::ASTCodeBody, use BasicBugReport with PathDiagnosticLocation exactly
as demonstrated. Do not construct PathSensitiveBugReport and do not fabricate
or pass a null ExplodedNode.
Repair the compiler error without changing which nodes the checker reports.
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate or include a project-local header.
"""


def build_augmentation_logic_prompt(kind, cpp, passed_cases, failed_case,
                                    check_result="", failure_history="",
                                    sibling_failures="", all_attempts=""):
    expectation = {
        "negative": "must report this case",
        "positive": "must not report this case",
    }.get(kind, "must stop crashing the analyzer on this case")
    return f"""Analyze a semantic failure in a CSA checker. The candidate {expectation}
without regressing any passed case. Return one JSON object with these keys:
root_cause, semantic_change, required_callbacks, preserved_behavior,
api_search_terms, and proposed_modification.
Current checker:
{cpp}
Passed cases:
{passed_cases}
Failed {kind} case:
{failed_case}
Complete checker result (expected/actual diagnostics, return code and logs):
{check_result}
Other cases that fail the same way (a fix that special-cases the target will be
rejected):
{sibling_failures}
Previous rejected attempts for this target:
{failure_history}
Lessons from other targets in this rule:
{all_attempts}

Return JSON only. Start your answer with `{{`. Do not write any prose before or
after the JSON.
"""


def build_augmentation_prompt(kind, rule_description, cpp, logic, context,
                              passed_cases, failed_case, check_result="",
                              failure_history="", checker_name="", frontend="",
                              rule_id="", diagnostic="", sibling_failures="",
                              all_attempts=""):
    headline = {
        "negative": "Improve this CSA checker for a false negative result.",
        "positive": "Improve this CSA checker for a false positive result.",
    }.get(kind, "Repair this CSA checker: it crashes or exits non-zero on the case below.")
    return f"""{headline}
Rule: {rule_description}
Implementation class: {checker_name}
Frontend: {frontend}
Rule identifier: {rule_id}
Required diagnostic: {diagnostic}
Augmentation logic: {logic}
CSA context: {context}
Current implementation:
{cpp}
Already passed cases:
{passed_cases}
Failed case:
{failed_case}
Complete checker result (expected/actual diagnostics, return code and logs):
{check_result}

## Other cases that fail the same way
{sibling_failures}

## Previous rejected attempts for this target
{failure_history}

## Lessons from other targets in this rule
{all_attempts}

{CALLBACK_FACTS}
Keep the implementation class, frontend, registration functions, analyzer API
version, and single-file plugin structure unchanged. The checker must emit the
configured diagnostic through the registered frontend; the diagnostic and rule
identifier do not have to appear as literal strings in every source location.
The target case must be fixed and every passed case is a regression contract.

Fix the general cause, not the specific target. The other cases listed above
fail the same way and a change that special-cases the target will be rejected.
Do not fix false positives by weakening, narrowing to a literal name, or
removing the report path: the negative cases above must continue to report.
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate a header.
"""
