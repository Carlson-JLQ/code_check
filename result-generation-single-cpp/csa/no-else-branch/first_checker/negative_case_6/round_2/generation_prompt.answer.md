I’m checking the checker surface and then I’ll wire the AST walk to flag only `if` chains that have at least one `else if` and no final `else`. The implementation will stay in one translation unit and use only the plugin-facing analyzer APIs you already provided.```cpp
#include "clang/AST/ASTContext.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/Basic/SourceLocation.h"
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

  static const IfStmt *getInnermostIf(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      Current = ElseIf;
    }
    return Current;
  }

  static bool hasElseIfChain(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        return Current != IS;
      Current = ElseIf;
    }
    return false;
  }

  static const IfStmt *getFirstIfInChain(const IfStmt *IS) {
    const IfStmt *First = IS;
    while (First) {
      const Stmt *Else = First->getElse();
      const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      First = First;
      break;
    }
    return IS;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)D;
    (void)AM;

    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch in if-else if chain",
                                     "GJB8114");

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D)) {
      Body = FD->getBody();
    } else if (const auto *MD = dyn_cast<CXXMethodDecl>(D)) {
      Body = MD->getBody();
    } else if (const auto *OD = dyn_cast<ObjCMethodDecl>(D)) {
      Body = OD->getBody();
    }
    if (!Body)
      return;

    struct Walker : public ConstStmtVisitor<Walker> {
      const GeneratedNoElseBranchChecker *Checker;
      BugReporter &BR;
      const BugType &BT;

      Walker(const GeneratedNoElseBranchChecker *Checker, BugReporter &BR,
             const BugType &BT)
          : Checker(Checker), BR(BR), BT(BT) {}

      void VisitStmt(const Stmt *S) {
        if (!S)
          return;
        for (const Stmt *Child : S->children())
          if (Child)
            Visit(Child);
      }

      void VisitIfStmt(const IfStmt *IS) {
        const IfStmt *Root = IS;
        while (const IfStmt *Parent = dyn_cast_or_null<IfStmt>(Root->getElse()))
          Root = Parent;

        const IfStmt *Cur = Root;
        bool SeenElseIf = false;
        while (Cur) {
          const Stmt *Else = Cur->getElse();
          const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
          if (!ElseIf)
            break;
          SeenElseIf = true;
          Cur = ElseIf;
        }

        if (SeenElseIf && !Cur->getElse()) {
          SourceLocation Loc = Cur->getIfLoc();
          if (Loc.isInvalid())
            Loc = Root->getIfLoc();

          auto R = std::make_unique<PathSensitiveBugReport>(
              BT, "禁止省略 if-else if 语句的 else 分支", BR.getErrorNode(Checker->BT->getCheckerManager().getContext().getState()),
              Loc);
          R->setDeclWithIssue(nullptr);
          BR.emitReport(std::move(R));
        }

        VisitStmt(IS->getThen());
        if (const Stmt *Else = IS->getElse())
          Visit(Else);
      }
    };

    Walker W(this, BR, *BT);
    W.Visit(Body);
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