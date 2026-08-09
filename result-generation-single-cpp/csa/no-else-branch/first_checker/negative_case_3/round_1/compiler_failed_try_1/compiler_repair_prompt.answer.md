I’ve got the failure mode: this checker is trying to use path-sensitive report APIs from an AST-body callback, and those mutators don’t exist in this Clang. I’m switching it to the minimal AST-only report path that this callback actually supports, while keeping the class and frontend names intact.I’m editing only the report construction and leaving the chain-walk logic in place. The key fix is to build `BugReport` directly from `BugType` and the `BugReporter` context, then emit it without the removed `PathSensitiveBugReport` methods.```cpp
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

  static const IfStmt *getOutermostIf(const IfStmt *If) {
    const IfStmt *Root = If;
    while (const auto *ParentIf = dyn_cast_or_null<IfStmt>(Root->getElse()))
      Root = ParentIf;
    return Root;
  }

  static const IfStmt *getLastElseIf(const IfStmt *If) {
    const IfStmt *Current = If;
    const IfStmt *LastElseIf = nullptr;

    while (const Stmt *Else = Current->getElse()) {
      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        break;
      LastElseIf = ElseIf;
      Current = ElseIf;
    }

    return LastElseIf ? LastElseIf : If;
  }

  void reportMissingElse(const IfStmt *If, BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch in if-else-if chain",
                                     "gjb8114.NoElseBranch");

    const IfStmt *Root = getOutermostIf(If);
    const IfStmt *ReportNode = getLastElseIf(Root);

    PathDiagnosticLocation Loc =
        PathDiagnosticLocation::createBegin(ReportNode, BR.getSourceManager());

    auto R = std::make_unique<BugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", Loc);
    R->addRange(ReportNode->getSourceRange());

    if (const DeclStmt *CondVar = Root->getConditionVariableDeclStmt())
      R->markInteresting(CondVar);

    BR.emitReport(std::move(R));
  }

  static void collectIfChains(const Stmt *S, BugReporter &BR,
                              const GeneratedNoElseBranchChecker &Checker) {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      if (!If->getElse())
        Checker.reportMissingElse(If, BR);
    }

    for (const Stmt *Child : S->children())
      collectIfChains(Child, BR, Checker);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D)) {
      if (const Stmt *Body = FD->getBody())
        collectIfChains(Body, BR, *this);
      return;
    }

    if (const auto *DC = dyn_cast_or_null<DeclContext>(D)) {
      for (const Decl *Inner : DC->decls()) {
        if (const auto *InnerFD = dyn_cast<FunctionDecl>(Inner)) {
          if (const Stmt *Body = InnerFD->getBody())
            collectIfChains(Body, BR, *this);
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
```