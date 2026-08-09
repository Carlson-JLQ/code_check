{
  "repair_steps": [
    "Do not instantiate `clang::ento::BugReport` directly. It is abstract, so `std::make_unique<BugReport>(...)` cannot compile.",
    "Create a concrete diagnostic object instead. In Static Analyzer checkers, that is typically `PathSensitiveBugReport`, constructed with the `BugType`, message, and a `PathDiagnosticLocation` or location-derived arguments.",
    "Replace the report construction site in `report(...)` with the concrete report class and pass the bug location for `Tail` in the form the constructor expects. Keep `BR.emitReport(...)` unchanged.",
    "If the current API surface does not provide a direct constructor match, build the report using the available Static Analyzer helper for bug reports in this version of Clang, rather than the abstract base type.",
    "Verify the checker still emits at the same AST location and that the report text remains unchanged after the type substitution."
  ],
  "api_search_terms": [
    "clang::ento::PathSensitiveBugReport",
    "clang::ento::BugReporter::emitReport",
    "clang::ento::BugType",
    "clang::ento::PathDiagnosticLocation",
    "clang::ento::BugReport constructor abstract static analyzer",
    "clang static analyzer concrete bug report class"
  ]
}