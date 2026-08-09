{
  "repair_steps": [
    "Remove the invalid `BR.getData()` argument when constructing `PathSensitiveBugReport`; `BugReporter` does not expose `getData()` in this API.",
    "Construct the report with the bug type and message only, then add the source range and emit it through `BR.emitReport(...)`.",
    "If you need analyzer context inside the report, obtain it from the checker callback context when available, not from `BugReporter`.",
    "Rebuild the plugin after the edit to confirm the checker compiles against the current CSA headers."
  ],
  "api_search_terms": [
    "clang::ento::BugReporter emitReport",
    "clang::ento::PathSensitiveBugReport constructor",
    "clang::ento::CheckerContext getState",
    "clang::ento::CheckerContext addTransition",
    "clang::ento::check::ASTCodeBody",
    "clang::ento::BugReporter API clang StaticAnalyzer current headers"
  ]
}