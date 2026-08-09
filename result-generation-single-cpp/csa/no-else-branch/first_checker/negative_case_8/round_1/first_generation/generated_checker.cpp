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

  static const IfStmt *getInnermostIfChainHead(const IfStmt *If) {
    const IfStmt *Current = If;
    while (Current) {
      const Stmt *Else = Current->getElse();
      if (!Else)
        break;

      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        break;

      Current = ElseIf;
    }
    return Current;
  }

  static bool chainContainsElseIf(const IfStmt *If) {
    const IfStmt *Current = If;
    while (Current) {
      const Stmt *Else = Current->getElse();
      if (!Else)
        return false;

      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        return false;

      return true;
    }
    return false;
  }

  static const Stmt *getBranchLocationStmt(const IfStmt *If) {
    const Stmt *Then = If->getThen();
    if (Then)
      return Then;
    return If->getCond();
  }

  void reportMissingFinalElse(const IfStmt *If, BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch", "GJB8114");

    const Stmt *LocStmt = getBranchLocationStmt(If);
    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", BR.getErrorNode(LocStmt->getBeginLoc()));
    R->addRange(LocStmt->getSourceRange());
    BR.emitReport(std::move(R));
  }

  void checkStmt(const Stmt *S, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      const IfStmt *Head = getInnermostIfChainHead(If);
      if (Head && chainContainsElseIf(Head) && !Head->getElse())
        reportMissingFinalElse(Head, BR);
    }

    for (const Stmt *Child : S->children())
      checkStmt(Child, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;
    if (!D)
      return;

    if (const auto *FD = dyn_cast<FunctionDecl>(D)) {
      if (const Stmt *Body = FD->getBody())
        checkStmt(Body, BR);
      return;
    }

    if (const auto *DC = dyn_cast<DeclContext>(D)) {
      for (const Decl *Child : DC->decls()) {
        if (const auto *FD = dyn_cast<FunctionDecl>(Child)) {
          if (const Stmt *Body = FD->getBody())
            checkStmt(Body, BR);
        }
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