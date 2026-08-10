#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ExprCXX.h"
#include "clang/AST/OperationKinds.h"
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
class GeneratedNoAssignmentInConditionChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Assignment in condition", "GJB8114"};

  void emitReport(const Expr *Violation, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    if (!Violation || !ADC)
      return;

    SourceLocation Loc = Violation->getBeginLoc();
    if (const auto *BO = dyn_cast<BinaryOperator>(Violation))
      Loc = BO->getOperatorLoc();
    else if (const auto *OCE = dyn_cast<CXXOperatorCallExpr>(Violation))
      Loc = OCE->getOperatorLoc();

    PathDiagnosticLocation PDL(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止将赋值语句作为逻辑表达式", PDL);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  const Expr *findAssignmentInExpr(const Expr *E) const {
    if (!E)
      return nullptr;

    const Expr *Stripped = E->IgnoreParenImpCasts();

    if (const auto *BO = dyn_cast<BinaryOperator>(Stripped)) {
      if (BO->isAssignmentOp())
        return Stripped;
    } else if (const auto *OCE = dyn_cast<CXXOperatorCallExpr>(Stripped)) {
      if (OCE->getOperator() == OO_Equal)
        return Stripped;
    }

    for (const Stmt *Child : Stripped->children()) {
      const auto *ChildExpr = dyn_cast<Expr>(Child);
      if (!ChildExpr)
        continue;
      if (const Expr *Found = findAssignmentInExpr(ChildExpr))
        return Found;
    }

    return nullptr;
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC,
                   BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      if (const Expr *Found = findAssignmentInExpr(IS->getCond()))
        emitReport(Found, ADC, BR);
    } else if (const auto *WS = dyn_cast<WhileStmt>(S)) {
      if (const Expr *Found = findAssignmentInExpr(WS->getCond()))
        emitReport(Found, ADC, BR);
    } else if (const auto *DS = dyn_cast<DoStmt>(S)) {
      if (const Expr *Found = findAssignmentInExpr(DS->getCond()))
        emitReport(Found, ADC, BR);
    } else if (const auto *FS = dyn_cast<ForStmt>(S)) {
      if (const Expr *Found = findAssignmentInExpr(FS->getCond()))
        emitReport(Found, ADC, BR);
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = ADC->getBody();
    if (!Body)
      return;

    inspectStmt(Body, ADC, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoAssignmentInConditionChecker>(
      "gjb8114.NoAssignmentInCondition",
      "Prohibits assignments used directly in logical conditions");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;