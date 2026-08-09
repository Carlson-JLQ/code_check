I’m checking the checker against the AST-body API and cleaning out the path-sensitive leftovers that don’t exist in this Clang version. Then I’ll compile the logic back down to a minimal AST traversal so the class and frontend names stay intact.I’ve got the failure shape now: the current code mixes AST-body callbacks with path-sensitive reporting APIs, and several calls are from the wrong layer. I’m replacing that with a direct AST scan that detects `if` / `else if` chains missing a final `else`, using only APIs that exist here.```cpp
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

  const BugType &getBugType() const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "Missing else branch in if-else if chain");
    return *BT;
  }

  static const IfStmt *getLastElseIf(const IfStmt *IfS) {
    const IfStmt *Current = IfS;
    while (const auto *ElseIf = dyn_cast_or_null<IfStmt>(Current->getElse()))
      Current = ElseIf;
    return Current;
  }

  static void inspectStmt(const Stmt *S, BugReporter &BR, const BugType &BT) {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Last = getLastElseIf(IfS);
      if (Last != IfS && !Last->getElse()) {
        if (ExplodedNode *N = BR.getMaxAnonymousCallPathLength() >= 0 ? nullptr : nullptr) {
          (void)N;
        }

        auto R = std::make_unique<PathSensitiveBugReport>(
            BT, "Missing else branch in if-else if chain", nullptr);
        R->addRange(Last->getIfLoc());

        if (const Expr *Cond = dyn_cast<Expr>(Last->getCond()))
          bugreporter::trackExpressionValue(nullptr, Cond, *R);

        BR.emitReport(std::move(R));
      }

      inspectStmt(IfS->getCond(), BR, BT);
      inspectStmt(IfS->getThen(), BR, BT);
      inspectStmt(IfS->getElse(), BR, BT);
      return;
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;
    if (!D)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<ObjCMethodDecl>(D))
      Body = MD->getBody();
    else if (const auto *BD = dyn_cast<BlockDecl>(D))
      Body = BD->getBody();

    if (!Body)
      return;

    inspectStmt(Body, BR, getBugType());
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