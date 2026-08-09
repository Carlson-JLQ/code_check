I’m checking the available AST and analyzer APIs, then I’ll wire the checker to inspect `if` chains structurally and emit the requested diagnostic at the right `if`.```cpp
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

namespace {

class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  mutable std::unique_ptr<BugType> BT;

  static const IfStmt *getEnclosingIfStmt(const Stmt *S) {
    if (!S)
      return nullptr;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body())
        if (const IfStmt *I = getEnclosingIfStmt(Child))
          return I;
      return nullptr;
    }

    if (const auto *I = dyn_cast<IfStmt>(S))
      return I;

    for (const Stmt *Child : S->children())
      if (const IfStmt *I = getEnclosingIfStmt(Child))
        return I;

    return nullptr;
  }

  static bool hasElseIfChainWithoutFinalElse(const IfStmt *Top) {
    if (!Top)
      return false;

    const IfStmt *Cur = Top;
    bool SawElseIf = false;

    while (Cur) {
      const Stmt *Else = Cur->getElse();
      if (!Else)
        return SawElseIf;

      const IfStmt *Next = dyn_cast<IfStmt>(Else);
      if (!Next)
        return false;

      SawElseIf = true;
      Cur = Next;
    }

    return false;
  }

  static const IfStmt *findMostSpecificViolatingIf(const Stmt *S) {
    if (!S)
      return nullptr;

    if (const auto *I = dyn_cast<IfStmt>(S)) {
      if (hasElseIfChainWithoutFinalElse(I))
        return I;
    }

    for (const Stmt *Child : S->children())
      if (const IfStmt *Found = findMostSpecificViolatingIf(Child))
        return Found;

    return nullptr;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    if (!BT)
      BT = std::make_unique<BugType>(
          this, "NoElseBranch", "gjb8114.NoElseBranch");

    const Stmt *Body = FD->getBody();
    const IfStmt *ViolatingIf = findMostSpecificViolatingIf(Body);
    if (!ViolatingIf)
      return;

    const IfStmt *ReportSite = ViolatingIf;
    while (const IfStmt *Parent = getEnclosingIfStmt(Body)) {
      (void)Parent;
      break;
    }

    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支",
        BR.GetPathDiagnosticLocation(ReportSite, BR.getSourceManager()));
    R->addRange(ReportSite->getIfLoc());

    BR.emitReport(std::move(R));
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
```