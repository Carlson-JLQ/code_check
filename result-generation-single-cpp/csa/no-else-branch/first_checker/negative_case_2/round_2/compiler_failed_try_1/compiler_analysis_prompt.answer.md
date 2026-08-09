I’m mapping the errors to the current Static Analyzer API, then I’ll return the minimal repair plan and the exact API terms that fit this checker style.{
  "repair_steps": [
    "Replace `std::make_unique<PathSensitiveBugReport>(...)` with a constructor call that matches the current API. `PathSensitiveBugReport` now requires an `ExplodedNode *errorNode` as the third argument, and optionally `PathDiagnosticLocation` and `Decl *` for uniqueness. Use the current predecessor node from the checker callback context, not `SourceLocation`.",
    "Change the checker entry point away from `checkASTCodeBody` if you need path-sensitive diagnostics from CFG nodes. `ASTCodeBody` gives you `Decl`, `AnalysisManager`, and `BugReporter`, but not the `ExplodedNode *` needed by `PathSensitiveBugReport`. Move the logic to a path-sensitive callback such as `checkPreStmt` or `checkBranchCondition` with `CheckerContext`.",
    "Stop calling removed `PathSensitiveBugReport` mutators. `setDeclWithIssue` and `setRange` are not available on this class in the current headers. If you need uniqueness, pass the declaration and diagnostic location through the constructor; if you need source range information, attach it through the reporting path available in the API you target, not by post-construction mutation.",
    "For a non-path-sensitive AST checker, use plain `BugReport` instead of `PathSensitiveBugReport`, and emit it through `BugReporter`. That matches the information available in `checkASTCodeBody` much better.",
    "If you keep the checker as AST-based, construct the report with `BugReport` plus a `SourceRange`/location strategy supported by `BugReporter`, and avoid any dependency on `ExplodedNode`.",
    "After the API migration, rebuild against the checked-in Clang headers and confirm whether the checker should remain `check::ASTCodeBody` or be converted to a path-sensitive checker. The current code mixes both models."
  ],
  "api_search_terms": [
    "clang::ento::PathSensitiveBugReport constructor ExplodedNode errorNode PathDiagnosticLocation DeclToUnique",
    "clang::ento::BugReport BugReporter addRange SourceRange",
    "clang::ento::check::ASTCodeBody vs check::PreStmt checker",
    "clang::ento::CheckerContext addTransition emitReport PathSensitiveBugReport",
    "clang::ento::BugReporter emitReport BugReport source range",
    "clang Static Analyzer report declaration with issue current API"
  ]
}