{
  "repair_steps": [
    "Replace `PathDiagnosticLocation::createBegin(IfS, AM.getSourceManager(), D)` with an overload that matches the real API. For this checker, the simplest fix is usually `PathDiagnosticLocation::createBegin(IfS, AM.getSourceManager(), AM.getAnalysisDeclContext())` if you have an `AnalysisDeclContext`, or `PathDiagnosticLocation::createBegin(IfS, AM.getSourceManager(), /*StackFrameOrAnalysisDeclContext*/ ...)` when using the stmt-based overload. Do not pass a `const Decl *` as the third argument to the stmt overload.",
    "Stop instantiating `BugReport` directly. `clang::ento::BugReport` is abstract, so `std::make_unique<BugReport>(...)` cannot compile. Use the concrete reporter type expected by the Static Analyzer, typically `std::make_unique<PathSensitiveBugReport>(*BT, message, location)`.",
    "Keep the report emission flow the same after switching to the concrete report class: construct the report, add the source range, then call `BR.emitReport(std::move(Report))`.",
    "If the chosen `PathDiagnosticLocation` overload needs an analysis context rather than a decl, thread the analysis context through `emitReport` from `checkASTCodeBody` instead of forcing a decl-based call site."
  ],
  "api_search_terms": [
    "clang::ento::PathSensitiveBugReport",
    "clang::ento::BugReport abstract getLocation getDeclWithIssue getUniqueingLocation getUniqueingDecl Profile",
    "clang::ento::PathDiagnosticLocation::createBegin Stmt SourceManager AnalysisDeclContext",
    "clang::ento::PathDiagnosticLocation::createBegin Decl SourceManager",
    "clang::ento::AnalysisManager getAnalysisDeclContext",
    "clang::ento::BugReporter emitReport PathSensitiveBugReport",
    "clang Static Analyzer bug report concrete class"
  ]
}