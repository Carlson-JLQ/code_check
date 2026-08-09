I’m checking the analyzer-side AST APIs available in the template and the retrieved context, then I’ll wire the checker to flag only `if` chains that have `else if` but no final `else`.```cpp
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

  static const IfStmt *getInnermostIf(const IfStmt *IfS) {
    while (IfS) {
      const Stmt *Else = IfS->getElse();
      const auto *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        return IfS;
      IfS = ElseIf;
    }
    return nullptr;
  }

  static bool hasElseIfChain(const IfStmt *IfS) {
    const IfStmt *Current = IfS;
    bool SawElseIf = false;

    while (Current) {
      const Stmt *Else = Current->getElse();
      const auto *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      SawElseIf = true;
      Current = ElseIf;
    }

    return SawElseIf;
  }

  static const Stmt *findMostSpecificLocation(const IfStmt *IfS) {
    const IfStmt *Innermost = getInnermostIf(IfS);
    if (!Innermost)
      return IfS;
    return Innermost->getIfLoc().isValid() ? Innermost : IfS;
  }

  void reportMissingElse(const IfStmt *IfS, AnalysisManager &AM,
                         BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this,
                                     "Missing final else branch",
                                     "GJB8114");

    const Stmt *LocStmt = findMostSpecificLocation(IfS);
    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", BR.getErrorNode(AM.getAnalysisDeclContext(), nullptr),
        LocStmt);
    BR.emitReport(std::move(R));
  }

  void checkStmtForIfChain(const Stmt *S, AnalysisManager &AM,
                           BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Outer = IfS;
      while (const auto *ParentIf = dyn_cast_or_null<IfStmt>(Outer->getElse()))
        Outer = ParentIf;

      if (hasElseIfChain(IfS) && !Outer->getElse())
        reportMissingElse(IfS, AM, BR);
    }

    for (const Stmt *Child : S->children())
      checkStmtForIfChain(Child, AM, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD)
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    checkStmtForIfChain(Body, AM, BR);
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