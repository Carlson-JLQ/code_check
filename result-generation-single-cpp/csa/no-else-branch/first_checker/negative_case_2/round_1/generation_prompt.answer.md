I’m checking the available CSA surface first so the checker matches the local analyzer style and only uses APIs we know are present. Next I’ll wire the structural AST walk for `if` / `else if` chains and make the diagnostic point at the final `if` in the chain that lacks an `else`.```cpp
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

  static const IfStmt *getInnermostIfChainEnd(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      if (!Else)
        return Current;

      const IfStmt *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        return nullptr;

      Current = ElseIf;
    }
    return nullptr;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch", "GJB8114");

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D)) {
      Body = FD->getBody();
    } else if (const auto *MD = dyn_cast<ObjCMethodDecl>(D)) {
      Body = MD->getBody();
    }

    if (!Body)
      return;

    std::vector<const Stmt *> WorkList;
    WorkList.push_back(Body);

    while (!WorkList.empty()) {
      const Stmt *S = WorkList.back();
      WorkList.pop_back();

      if (!S)
        continue;

      if (const auto *IS = dyn_cast<IfStmt>(S)) {
        const IfStmt *Violation = getInnermostIfChainEnd(IS);
        if (Violation && !Violation->getElse()) {
          ExplodedNode *N = nullptr;
          if (BugReport *R = BR.createBasicReport(*BT,
                                                  "禁止省略 if-else if 语句的 else 分支",
                                                  N)) {
            R->addRange(Violation->getIfLoc());
            BR.emitReport(std::move(R));
          }
        }

        if (const Stmt *Then = IS->getThen())
          WorkList.push_back(Then);
        if (const Stmt *Else = IS->getElse())
          WorkList.push_back(Else);
        continue;
      }

      for (const Stmt *Child : S->children()) {
        if (Child)
          WorkList.push_back(Child);
      }
    }
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