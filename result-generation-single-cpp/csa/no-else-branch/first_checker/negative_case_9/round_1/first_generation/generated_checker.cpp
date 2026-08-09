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

  static const IfStmt *findOutermostIf(const IfStmt *IS) {
    if (!IS)
      return nullptr;

    const IfStmt *Current = IS;
    while (true) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        break;

      const auto *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        break;

      Current = ElseIf;
    }
    return Current;
  }

  static void collectIfChains(const Stmt *S, std::vector<const IfStmt *> &Out) {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Head = findOutermostIf(IS);
      if (Head)
        Out.push_back(Head);

      collectIfChains(IS->getCond(), Out);
      collectIfChains(IS->getThen(), Out);
      collectIfChains(IS->getElse(), Out);
      return;
    }

    for (const Stmt *Child : S->children())
      collectIfChains(Child, Out);
  }

  bool chainRequiresElse(const IfStmt *IS) const {
    if (!IS)
      return false;

    const IfStmt *Current = IS;
    bool SawElseIf = false;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return SawElseIf;

      const auto *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return false;

      SawElseIf = true;
      Current = ElseIf;
    }
    return false;
  }

  void reportMissingElse(const IfStmt *IS, AnalysisManager &AM,
                         BugReporter &BR) const {
    if (!IS || !BT)
      return;

    const SourceManager &SM = AM.getSourceManager();
    const Stmt *Anchor = IS->getIfLoc().isValid() ? cast<Stmt>(IS) : cast<Stmt>(IS);
    SourceLocation Loc = IS->getElseLoc().isValid() ? IS->getElseLoc() : IS->getIfLoc();
    if (!Loc.isValid())
      Loc = IS->getBeginLoc();

    if (!Loc.isValid())
      return;

    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", nullptr);
    R->markInteresting(Loc);
    R->addRange(SourceRange(IS->getBeginLoc(), IS->getEndLoc()));
    BR.emitReport(std::move(R));
    (void)SM;
    (void)Anchor;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch", "gjb8114");

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    std::vector<const IfStmt *> Chains;
    collectIfChains(FD->getBody(), Chains);

    for (const IfStmt *Head : Chains) {
      if (!Head)
        continue;
      if (!chainRequiresElse(Head))
        continue;

      const IfStmt *Outermost = findOutermostIf(Head);
      if (!Outermost)
        continue;

      if (Outermost->getElse())
        continue;

      reportMissingElse(Outermost, AM, BR);
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