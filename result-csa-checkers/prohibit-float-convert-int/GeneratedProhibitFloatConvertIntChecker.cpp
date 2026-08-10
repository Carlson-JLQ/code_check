#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
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
class GeneratedProhibitFloatConvertIntChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "gjb8114-r-1-10-1", "GJB8114"};

  static bool isIntegerVariableLHS(const Expr *LHS) {
    if (!LHS)
      return false;

    const Expr *E = LHS->IgnoreParenImpCasts();
    const auto *DRE = dyn_cast<DeclRefExpr>(E);
    if (!DRE || !isa<VarDecl>(DRE->getDecl()))
      return false;

    QualType T = E->getType();
    return !T.isNull() && T->isIntegerType();
  }

  static bool isIntegerVariableDecl(const VarDecl *VD) {
    if (!VD)
      return false;

    QualType T = VD->getType();
    return !T.isNull() && T->isIntegerType();
  }

  static bool isWholeRHSExplicitlyCast(const Expr *RHS) {
    if (!RHS)
      return false;

    return isa<ExplicitCastExpr>(RHS->IgnoreParenImpCasts());
  }

  static bool isFloatingExpression(const Expr *RHS) {
    if (!RHS)
      return false;

    const Expr *E = RHS->IgnoreParenImpCasts();
    QualType T = E->getType();
    return !T.isNull() && T->isRealFloatingType();
  }

  static bool isViolationForIntegerDestination(const Expr *RHS) {
    if (!RHS)
      return false;

    if (isWholeRHSExplicitlyCast(RHS))
      return false;

    return isFloatingExpression(RHS);
  }

  static bool isViolation(const BinaryOperator *BO) {
    if (!BO || BO->getOpcode() != BO_Assign)
      return false;

    if (!isIntegerVariableLHS(BO->getLHS()))
      return false;

    return isViolationForIntegerDestination(BO->getRHS());
  }

  static bool isViolation(const VarDecl *VD) {
    if (!isIntegerVariableDecl(VD) || !VD->hasInit())
      return false;

    return isViolationForIntegerDestination(VD->getInit());
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止浮点数变量赋给整型变量", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC,
                   BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (isViolation(BO))
        emitASTReport(BO, ADC, BR);
    } else if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (isViolation(VD))
          emitASTReport(DS, ADC, BR);
      }
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

    inspectStmt(ADC->getBody(), ADC, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedProhibitFloatConvertIntChecker>(
      "gjb8114.ProhibitFloatConvertInt",
      "gjb8114-r-1-10-1: 禁止浮点数变量赋给整型变量");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;