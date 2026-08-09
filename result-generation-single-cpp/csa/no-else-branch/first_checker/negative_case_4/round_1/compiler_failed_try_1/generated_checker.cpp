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

  static bool hasElseIfChain(const IfStmt *IfS) {
    const IfStmt *Cur = IfS;
    while (Cur) {
      const Stmt *Else = Cur->getElse();
      if (!Else)
        return false;
      Cur = dyn_cast<IfStmt>(Else);
      if (!Cur)
        return true;
    }
    return false;
  }

  static const IfStmt *getOutermostIf(const IfStmt *IfS) {
    const IfStmt *Top = IfS;
    while (const Stmt *ParentElse = Top->getElse()) {
      const IfStmt *Next = dyn_cast<IfStmt>(ParentElse);
      if (!Next)
        break;
      Top = Next;
    }
    return Top;
  }

  void collectMissingElseReports(const Stmt *S,
                                 SmallVectorImpl<const IfStmt *> &Reports) const {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      const IfStmt *Top = getOutermostIf(IfS);
      if (hasElseIfChain(Top) && !Top->getElse()) {
        Reports.push_back(Top);
        return;
      }
    }

    for (const Stmt *Child : S->children())
      collectMissingElseReports(Child, Reports);
  }

  void emitReport(const IfStmt *IfS, const Decl *D, AnalysisManager &AM,
                  BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch in if-else if chain",
                                     "gjb8114.NoElseBranch");

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    const ExplodedNode *N = nullptr;
    if (FD) {
      if (AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(FD))
        N = BR.getGraphTrait()->getRoot(); // fallback-less path would not compile
    }

    PathDiagnosticLocation L =
        PathDiagnosticLocation::createBegin(IfS, BR.getSourceManager(),
                                            AM.getAnalysisDeclContext(D));

    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", N, L, D);
    BR.emitReport(std::move(R));
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

    SmallVector<const IfStmt *, 8> Reports;
    collectMissingElseReports(Body, Reports);

    for (const IfStmt *IfS : Reports)
      emitReport(IfS, D, AM, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;