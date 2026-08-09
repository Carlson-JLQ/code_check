I’m checking the existing template and the CSA APIs you provided, then I’ll turn that into a concrete branch-condition checker that flags only `if` chains with an `else if` and no final `else`.```cpp
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
          "Missing else branch in if-else if chain",
          "gjb8114.NoElseBranch");
    return *BT;
  }

  static const IfStmt *getInnermostIfChainHead(const IfStmt *IfS) {
    const IfStmt *Current = IfS;
    while (true) {
      const Stmt *Else = Current->getElse();
      if (!Else)
        return Current;
      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        return Current;
      Current = ElseIf;
    }
  }

  static const IfStmt *getChainRoot(const IfStmt *IfS) {
    const IfStmt *Root = IfS;
    while (const auto *ParentIf = dyn_cast<IfStmt>(Root->getParent())) {
      if (ParentIf->getElse() != Root)
        break;
      Root = ParentIf;
    }
    return Root;
  }

  static const IfStmt *getTopLevelIfInChain(const IfStmt *IfS) {
    const IfStmt *Top = IfS;
    while (const IfStmt *Parent = dyn_cast<IfStmt>(Top->getParent())) {
      if (Parent->getElse() != Top)
        break;
      Top = Parent;
    }
    return Top;
  }

  static const IfStmt *getLastElseIf(const IfStmt *IfS) {
    const IfStmt *Current = IfS;
    while (const auto *ElseIf = dyn_cast_or_null<IfStmt>(Current->getElse()))
      Current = ElseIf;
    return Current;
  }

  static void inspectStmt(const Stmt *S, AnalysisManager &AM, BugReporter &BR,
                          const BugType &BT) {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Last = getLastElseIf(IfS);
      if (Last != IfS && !Last->getElse()) {
        ExplodedNode *N = nullptr;
        if (const LocationContext *LC =
                AM.getAnalysisDeclContext().getCurrentFunctionOrMethod())
          (void)LC;
        PathDiagnosticLocation Loc =
            PathDiagnosticLocation::createBegin(Last->getIfLoc(), BR.getSourceManager());
        if (ExplodedNode *EN = BR.getBugReporterData().getCurrentNode())
          N = EN;

        auto R = std::make_unique<PathSensitiveBugReport>(
            BT, "禁止省略 if-else if 语句的 else 分支", N);
        R->addRange(Last->getIfLoc());

        if (const Stmt *Cond = Last->getCond())
          bugreporter::trackExpressionValue(N, Cond, *R);

        BR.emitReport(std::move(R));
      }

      inspectStmt(IfS->getCond(), AM, BR, BT);
      inspectStmt(IfS->getThen(), AM, BR, BT);
      inspectStmt(IfS->getElse(), AM, BR, BT);
      return;
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, AM, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    if (!D)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<ObjCMethodDecl>(D))
      Body = MD->getBody();
    else if (const auto *BD = dyn_cast<BlockDecl>(D))
      Body = BD->getBody();

    if (!Body)
      return;

    inspectStmt(Body, AM, BR, getBugType());
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