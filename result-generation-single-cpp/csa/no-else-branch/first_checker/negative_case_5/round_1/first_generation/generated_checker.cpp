#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

#include <vector>

using namespace clang;
using namespace ento;

namespace {

class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  mutable std::unique_ptr<BugType> BT;

  static const IfStmt *getEnclosingIfStmt(const Stmt *S) {
    if (!S)
      return nullptr;
    return dyn_cast<IfStmt>(S);
  }

  static bool hasElseIfBranch(const IfStmt *IfS) {
    if (!IfS)
      return false;
    const IfStmt *Current = IfS;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return false;
      const IfStmt *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return false;
      Current = ElseIf;
    }
    return true;
  }

  static const IfStmt *getOuterMostChainHead(const IfStmt *IfS) {
    if (!IfS)
      return nullptr;
    const IfStmt *Head = IfS;
    while (true) {
      const Stmt *ParentElse = Head->getParentStmt();
      const IfStmt *ParentIf = dyn_cast_or_null<IfStmt>(ParentElse);
      if (!ParentIf || ParentIf->getElse() != Head)
        break;
      Head = ParentIf;
    }
    return Head;
  }

  static const Stmt *getMissingElseReportLocation(const IfStmt *ChainHead) {
    if (!ChainHead)
      return nullptr;
    const IfStmt *Current = ChainHead;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return Current->getIfLoc().getLocWithOffset(0), Current;
      const IfStmt *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return nullptr;
      Current = ElseIf;
    }
    return nullptr;
  }

  void reportMissingElse(const IfStmt *ChainHead, AnalysisManager &AM,
                         BugReporter &BR) const {
    if (!ChainHead)
      return;

    if (!BT)
      BT = std::make_unique<BugType>(
          this, "Missing else in if-else if chain",
          categories::LogicError);

    const Stmt *ReportStmt = getMissingElseReportLocation(ChainHead);
    if (!ReportStmt)
      return;

    ExplodedNode *N = nullptr;
    ProgramPoint PP = ProgramPoint(ReportStmt, ProgramPoint::PostStmtKind,
                                   AM.getAnalysisDeclContext());
    (void)PP;

    PathDiagnosticLocation L =
        PathDiagnosticLocation::createBegin(const_cast<Stmt *>(ReportStmt),
                                            AM.getSourceManager(),
                                            AM.getAnalysisDeclContext());

    BR.EmitBasicReport(AM.getCurrentAnalysisDeclContext()->getDecl(), this,
                       "禁止省略 if-else if 语句的 else 分支", "gjb8114-r-1-4-1",
                       "禁止省略 if-else if 语句的 else 分支", L);
    (void)N;
  }

  class IfChainVisitor : public RecursiveASTVisitor<IfChainVisitor> {
    const GeneratedNoElseBranchChecker &Checker;
    AnalysisManager &AM;
    BugReporter &BR;

  public:
    IfChainVisitor(const GeneratedNoElseBranchChecker &Checker,
                   AnalysisManager &AM, BugReporter &BR)
        : Checker(Checker), AM(AM), BR(BR) {}

    bool VisitIfStmt(IfStmt *IfS) {
      if (!IfS)
        return true;

      if (!hasElseIfBranch(IfS))
        return true;

      const IfStmt *Head = getOuterMostChainHead(IfS);
      if (!Head)
        return true;

      const Stmt *ElsePart = Head->getElse();
      if (ElsePart)
        return true;

      Checker.reportMissingElse(Head, AM, BR);
      return true;
    }
  };

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)BR;
    if (!D)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<CXXMethodDecl>(D))
      Body = MD->getBody();
    else if (const auto *OD = dyn_cast<BlockDecl>(D))
      Body = OD->getBody();

    if (!Body)
      return;

    IfChainVisitor Visitor(*this, AM, BR);
    Visitor.TraverseStmt(const_cast<Stmt *>(Body));
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114.NoElseBranch",
                                                     "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;