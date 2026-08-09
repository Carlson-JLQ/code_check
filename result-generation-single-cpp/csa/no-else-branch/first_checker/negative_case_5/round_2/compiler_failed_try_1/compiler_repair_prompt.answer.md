I’m correcting the checker to match the AST-only callback it already uses, which means replacing the invalid path-sensitive report construction with a plain `BugReport` and keeping the registration/class names intact.I’ve got the shape of the fix: the current code is doing path-sensitive reporting from `checkASTCodeBody`, which cannot work because that callback never gives an `ExplodedNode`. I’m editing just the report creation and leaving the rest of the checker structure alone.```cpp
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

    auto R = std::make_unique<BugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", BR.getDataStore());
    R->addRange(ViolatingIf->getIfLoc());

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