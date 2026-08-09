I’m checking the checker shape first, then I’ll patch the report path to use APIs that actually exist for `checkASTCodeBody`.```cpp
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

  static void collectMissingElseIfs(const Stmt *S,
                                    SmallVectorImpl<const IfStmt *> &Out) {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      const IfStmt *ChainHead = If;
      while (const auto *Nested = dyn_cast<IfStmt>(ChainHead->getElse()))
        ChainHead = Nested;

      if (If != ChainHead) {
        for (const Stmt *Child : S->children())
          collectMissingElseIfs(Child, Out);
        return;
      }

      bool SawElseIf = false;
      const IfStmt *Current = If;
      while (const auto *CurIf = dyn_cast<IfStmt>(Current)) {
        const Stmt *Else = CurIf->getElse();
        if (!Else) {
          if (SawElseIf)
            Out.push_back(CurIf);
          break;
        }
        if (isa<IfStmt>(Else)) {
          SawElseIf = true;
          Current = cast<IfStmt>(Else);
          continue;
        }
        break;
      }
    }

    for (const Stmt *Child : S->children())
      collectMissingElseIfs(Child, Out);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch", "gjb8114");

    SmallVector<const IfStmt *, 8> Violations;
    collectMissingElseIfs(FD->getBody(), Violations);

    for (const IfStmt *If : Violations) {
      const Stmt *ElseLocStmt = If->getElseLoc().isValid() ? If->getElse() : If;
      SourceLocation Loc = ElseLocStmt ? ElseLocStmt->getBeginLoc()
                                       : If->getIfLoc();
      if (!Loc.isValid())
        Loc = If->getIfLoc();

      auto R = std::make_unique<BugReport>(
          *BT, "禁止省略 if-else if 语句的 else 分支");
      R->setDeclWithIssue(FD);
      R->addRange(If->getSourceRange());
      R->markInteresting(Loc);
      BR.emitReport(std::move(R));
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