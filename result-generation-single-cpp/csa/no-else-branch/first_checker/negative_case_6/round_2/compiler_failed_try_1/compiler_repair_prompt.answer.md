I’m updating the checker to use the analyzer’s concrete report type and removing the unsupported mutator call, while keeping the checker class and registration names intact.I’ve got the shape of the fix: keep the AST traversal, but emit a concrete `PathSensitiveBugReport` and let the report constructor carry the location. I’m checking the local API surface once more before patching so the constructor signature matches this Clang build.```cpp
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

  static const IfStmt *getOutermostIf(const IfStmt *IS) {
    const IfStmt *Root = IS;
    while (Root) {
      const Stmt *Else = Root->getElse();
      const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      Root = ElseIf;
    }
    return Root;
  }

  static void checkStmt(const Stmt *S, const GeneratedNoElseBranchChecker *Checker,
                        BugReporter &BR, const BugType &BT) {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Root = getOutermostIf(IS);
      const IfStmt *Current = Root;
      bool HasElseIf = false;

      while (Current) {
        const Stmt *Else = Current->getElse();
        const IfStmt *ElseIf = dyn_cast_or_null<IfStmt>(Else);
        if (!ElseIf)
          break;
        HasElseIf = true;
        Current = ElseIf;
      }

      if (HasElseIf && !Current->getElse()) {
        SourceLocation Loc = Current->getIfLoc();
        if (Loc.isInvalid())
          Loc = Root->getIfLoc();

        PathDiagnosticLocation PDL =
            PathDiagnosticLocation::createBegin(Loc, BR.getSourceManager());

        auto R = std::make_unique<PathSensitiveBugReport>(
            BT, "禁止省略 if-else if 语句的 else 分支", PDL);
        if (Loc.isValid())
          R->addRange(SourceRange(Loc));
        BR.emitReport(std::move(R));
      }
    }

    for (const Stmt *Child : S->children())
      checkStmt(Child, Checker, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
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

    checkStmt(Body, this, BR, *BT);
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