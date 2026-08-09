I’m correcting this by aligning the checker with the AST-body callback it already uses, and removing the invalid path-sensitive node creation. Next I’m checking the local file for any other API mismatches so the fix stays minimal and keeps the existing class and registration names intact.```cpp
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

  static const IfStmt *findOutermostIfChain(const IfStmt *S) {
    const IfStmt *Top = S;
    while (const Stmt *Parent = Top->getElse()) {
      const IfStmt *ElseIf = dyn_cast<IfStmt>(Parent);
      if (!ElseIf)
        break;
      Top = ElseIf;
    }
    return Top;
  }

  static bool hasElseIfBranch(const IfStmt *S) {
    if (!S)
      return false;
    const IfStmt *Top = findOutermostIfChain(S);
    for (const IfStmt *Cur = Top; Cur; Cur = dyn_cast_or_null<IfStmt>(Cur->getElse())) {
      if (Cur != Top)
        return true;
      if (!Cur->getElse())
        break;
    }
    return false;
  }

  static const IfStmt *findMostSpecificMissingElse(const Stmt *S) {
    const IfStmt *Result = nullptr;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      if (hasElseIfBranch(IS) && !IS->getElse())
        Result = IS;

      if (const Stmt *Then = IS->getThen()) {
        if (const IfStmt *Nested = findMostSpecificMissingElse(Then))
          Result = Nested;
      }
      if (const Stmt *Else = IS->getElse()) {
        if (const IfStmt *Nested = findMostSpecificMissingElse(Else))
          Result = Nested;
      }
      return Result;
    }

    for (const Stmt *Child : S->children()) {
      if (!Child)
        continue;
      if (const IfStmt *Nested = findMostSpecificMissingElse(Child))
        Result = Nested;
    }
    return Result;
  }

  void reportMissingElse(const IfStmt *IS, BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch", "gjb8114");

    const SourceLocation Loc = IS->getIfLoc();
    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", BR.getSourceManager().getLocForEndOfFile(BR.getSourceManager().getMainFileID()));
    R->addRange(SourceRange(Loc, Loc));
    BR.emitReport(std::move(R));
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const Decl *CodeDecl = D;
    if (!CodeDecl)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(CodeDecl))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<ObjCMethodDecl>(CodeDecl))
      Body = MD->getBody();
    else if (const auto *BD = dyn_cast<BlockDecl>(CodeDecl))
      Body = BD->getBody();
    else
      return;

    if (!Body)
      return;

    const IfStmt *Violation = findMostSpecificMissingElse(Body);
    if (!Violation)
      return;

    reportMissingElse(Violation, BR);
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