I’m checking the checker against the current CSA APIs and will trim it back to what `check::ASTCodeBody` can actually emit. The fix should stay inside the existing class and registration names.```cpp
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

  static const IfStmt *skipSingleBlock(const Stmt *S) {
    if (!S)
      return nullptr;

    if (const auto *Sub = dyn_cast<IfStmt>(S))
      return Sub;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body()) {
        if (const auto *Nested = skipSingleBlock(Child))
          return Nested;
      }
    }

    return nullptr;
  }

  static const IfStmt *getInnermostIfChainTail(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return Current;

      const IfStmt *NestedIf = skipSingleBlock(ElsePart);
      if (!NestedIf)
        return nullptr;

      Current = NestedIf;
    }
    return nullptr;
  }

  void report(const IfStmt *Tail, AnalysisManager &AM, BugReporter &BR) const {
    (void)AM;

    if (!BT)
      BT = std::make_unique<BugType>(this, "Missing final else branch", "GJB8114");

    auto R = std::make_unique<BugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", Tail);
    BR.emitReport(std::move(R));
  }

  void scanStmt(const Stmt *S, AnalysisManager &AM, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Tail = getInnermostIfChainTail(IS);
      if (Tail && Tail != IS && Tail->getElse() == nullptr)
        report(Tail, AM, BR);

      scanStmt(IS->getThen(), AM, BR);
      scanStmt(IS->getElse(), AM, BR);
      return;
    }

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body())
        scanStmt(Child, AM, BR);
      return;
    }

    if (const auto *LS = dyn_cast<LabelStmt>(S)) {
      scanStmt(LS->getSubStmt(), AM, BR);
      return;
    }

    if (const auto *WS = dyn_cast<WhileStmt>(S)) {
      scanStmt(WS->getBody(), AM, BR);
      return;
    }

    if (const auto *DoS = dyn_cast<DoStmt>(S)) {
      scanStmt(DoS->getBody(), AM, BR);
      return;
    }

    if (const auto *FS = dyn_cast<ForStmt>(S)) {
      scanStmt(FS->getBody(), AM, BR);
      return;
    }

    if (const auto *SS = dyn_cast<SwitchStmt>(S)) {
      scanStmt(SS->getBody(), AM, BR);
      return;
    }

    if (const auto *MS = dyn_cast<CaseStmt>(S)) {
      scanStmt(MS->getSubStmt(), AM, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DefaultStmt>(S)) {
      scanStmt(DS->getSubStmt(), AM, BR);
      return;
    }

    if (const auto *AS = dyn_cast<AttributedStmt>(S)) {
      scanStmt(AS->getSubStmt(), AM, BR);
      return;
    }
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