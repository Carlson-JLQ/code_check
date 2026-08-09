"""Prompt builders for the CodeQL-shaped CSA generation lifecycle."""


def build_logic_prompt(rule_description, test_code):
    return f"""Extract a JSON list of detection logic units for a Clang Static Analyzer checker.
Rule: {rule_description}
Negative test:
{test_code}
Each unit must contain intent, trigger, constraints, and CSA API search terms.
Return JSON only.
"""


def build_first_checker_prompt(
    rule_description,
    test_code,
    logic,
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
Negative test:
{test_code}
Retrieved CSA MetaOps:
{logic}
Retrieved CSA APIs:
{api_refs}
Known compiling plugin template implementation:
```cpp
{template_cpp}
```
Implement the stated rule rather than the empty callback in the structural
template. Inspect nested syntax where the rule requires it and report the most
specific violating source location. Export clang_registerCheckers and
clang_analyzerAPIVersionString. Keep the entire plugin in this C++ file.
Use only headers and APIs demonstrated by the template or retrieved context.
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
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate or include a project-local header.
"""


def build_augmentation_logic_prompt(kind, cpp, passed_cases, failed_case,
                                    check_result=""):
    expectation = "must report this case" if kind == "negative" else "must not report this case"
    return f"""Return JSON logic for improving a CSA checker. The candidate {expectation}
without regressing passed cases.
Current checker:
{cpp}
Passed cases:
{passed_cases}
Failed {kind} case:
{failed_case}
Complete checker result (expected/actual diagnostics, return code and logs):
{check_result}
"""


def build_augmentation_prompt(kind, rule_description, cpp, logic, context,
                              passed_cases, failed_case, check_result=""):
    return f"""Improve this CSA checker for a false {kind} result.
Rule: {rule_description}
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
Keep the implementation class and frontend unchanged. Return exactly one C++
implementation in a fenced cpp code block. Do not generate a header.
"""
