I’m checking the available Clang analyzer hooks and then I’ll wire the checker to the branch-condition callback so it flags only `if` chains that actually contain an `else if` and lack a final `else`.```cpp
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {
class GeneratedNoElseBranchChecker : public Checker<check::BranchCondition> {
  mutable std::unique_ptr<BugType> BT;

  static const IfStmt *getTopLevelIf(const Stmt *Condition) {
    return dyn_cast_or_null<IfStmt>(Condition);
  }

  static const IfStmt *getFinalElseIf(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const IfStmt *NestedIf = dyn_cast_or_null<IfStmt>(Else);
      if (!NestedIf)
        break;
      Current = NestedIf;
    }
    return Current;
  }

  static bool hasElseIfChain(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const IfStmt *NestedIf = dyn_cast_or_null<IfStmt>(Else);
      if (!NestedIf)
        break;
      return true;
    }
    return false;
  }

public:
  void checkBranchCondition(const Stmt *Condition, CheckerContext &C) const {
    const IfStmt *TopIf = getTopLevelIf(Condition);
    if (!TopIf)
      return;

    const IfStmt *FinalIf = getFinalElseIf(TopIf);
    if (!FinalIf)
      return;

    if (!hasElseIfChain(TopIf))
      return;

    if (FinalIf->getElse())
      return;

    if (!BT)
      BT.reset(new BugType(this, "NoElseBranch", "gjb8114"));

    ExplodedNode *N = C.generateNonFatalErrorNode();
    if (!N)
      return;

    auto Report =
        std::make_unique<PathSensitiveBugReport>(*BT,
                                                 "禁止省略 if-else if 语句的 else 分支",
                                                 N);
    Report->addRange(FinalIf->getIfLoc());
    C.emitReport(std::move(Report));
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114.NoElseBranch",
                                                    "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
```