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
      BT = std::make_unique<BugType>(this, "No else branch in if-else if chain",
                                     "Control Flow");
    return *BT;
  }

  static const IfStmt *getInnermostIf(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (const auto *Nested = dyn_cast_or_null<IfStmt>(Current->getElse()))
      Current = Nested;
    return Current;
  }

  static bool hasElseIfChain(const IfStmt *IS) {
    const IfStmt *Current = IS;
    bool HasElseIf = false;
    while (const auto *Nested = dyn_cast_or_null<IfStmt>(Current->getElse())) {
      HasElseIf = true;
      Current = Nested;
    }
    return HasElseIf;
  }

  static void scanStmt(const Stmt *S, BugReporter &BR, const BugType &BT) {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      if (hasElseIfChain(IS)) {
        const IfStmt *Innermost = getInnermostIf(IS);
        if (!Innermost->getElse()) {
          auto Report = std::make_unique<PathSensitiveBugReport>(
              BT, "禁止省略 if-else if 语句的 else 分支", BR.getErrorNode());
          Report->addRange(IS->getSourceRange());
          BR.emitReport(std::move(Report));
        }
      }

      scanStmt(IS->getCond(), BR, BT);
      scanStmt(IS->getThen(), BR, BT);
      scanStmt(IS->getElse(), BR, BT);
      return;
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    scanStmt(FD->getBody(), BR, getBugType());
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;