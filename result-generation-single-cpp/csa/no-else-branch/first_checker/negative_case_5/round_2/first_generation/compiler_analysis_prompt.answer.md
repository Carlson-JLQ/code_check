{
  "repair_steps": [
    "Remove the call to `BR.GetPathDiagnosticLocation(...)`. That API is not available on `clang::ento::BugReporter` in this Clang version, which is the direct compile failure.",
    "Construct the path diagnostic location from the statement/AST location instead of asking `BugReporter` for it. For this checker, using `ReportSite->getIfLoc()` as the report location is enough for a valid `PathSensitiveBugReport`.",
    "Keep the report creation minimal and version-stable: `auto R = std::make_unique<PathSensitiveBugReport>(*BT, \"...\", ReportSite->getIfLoc());` then `R->addRange(ReportSite->getIfLoc());` and `BR.emitReport(std::move(R));`.",
    "Delete the dead `while (const IfStmt *Parent = getEnclosingIfStmt(Body))` block. It never walks parents, never changes `ReportSite`, and only adds noise. It is not part of the fix, but it is misleading and should be removed while touching this code.",
    "If you want a more precise location later, search the local analyzer headers for the current helper used to translate a `SourceLocation` into a path diagnostic location, but do not depend on `BugReporter` having that member."
  ],
  "api_search_terms": [
    "clang::ento::BugReporter PathDiagnosticLocation current API",
    "clang::ento::PathSensitiveBugReport constructor SourceLocation",
    "clang Static Analyzer report location from SourceLocation",
    "PathDiagnosticLocation getLocation SourceManager",
    "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h PathDiagnosticLocation"
  ]
}