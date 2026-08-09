I’m checking the available analyzer hooks and then I’ll wire the checker to the smallest source location that proves the missing final `else`. The implementation will stay in one C++ file and use only the APIs already in scope.```cpp
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
      BT = std::make_unique<BugType>(
          this, "Missing final else branch in if-else if chain",
          "gjb8114.NoElseBranch");
    return *BT;
  }

  static const IfStmt *asIfStmt(const Stmt *S) {
    return dyn_cast_or_null<IfStmt>(S);
  }

  static const Stmt *getInnermostElseIfChainStart(const IfStmt *TopIf) {
    const IfStmt *Current = TopIf;
    while (true) {
      const Stmt *Else = Current->getElse();
      const IfStmt *ElseIf = asIfStmt(Else);
      if (!ElseIf)
        return Current;
      Current = ElseIf;
    }
  }

  static bool hasElseIfBranch(const IfStmt *TopIf) {
    const IfStmt *Current = TopIf;
    bool SawElseIf = false;
    while (const Stmt *Else = Current->getElse()) {
      const IfStmt *ElseIf = asIfStmt(Else);
      if (!ElseIf)
        break;
      SawElseIf = true;
      Current = ElseIf;
    }
    return SawElseIf;
  }

  static const Stmt *getViolationLocationStmt(const IfStmt *TopIf) {
    return getInnermostElseIfChainStart(TopIf);
  }

  void checkStmtForIfChain(const Stmt *S, AnalysisManager &AM,
                           BugReporter &BR) const {
    (void)AM;

    const IfStmt *IS = asIfStmt(S);
    if (!IS)
      return;

    if (!hasElseIfBranch(IS))
      return;

    const Stmt *Innermost = getViolationLocationStmt(IS);
    if (Innermost->getElse())
      return;

    ExplodedNode *N = BR.getStmtVisitor().getCurrentNode();
    if (!N)
      return;

    auto R = std::make_unique<PathSensitiveBugReport>(
        getBugType(),
        "禁止省略 if-else if 语句的 else 分支",
        N);
    R->addRange(Innermost->getSourceRange());
    BR.emitReport(std::move(R));
  }

  void scanStmt(const Stmt *S, AnalysisManager &AM, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S))
      checkStmtForIfChain(IS, AM, BR);

    for (const Stmt *Child : S->children())
      scanStmt(Child, AM, BR);
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

    scanStmt(Body, AM, BR);
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