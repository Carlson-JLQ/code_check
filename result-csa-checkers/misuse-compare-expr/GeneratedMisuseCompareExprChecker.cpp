#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/RecursiveASTVisitor.h"
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

class GeneratedMisuseCompareExprChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "gjb8114-r-1-2-5", "GJB8114"};

  static bool isBitwiseOrShiftOp(BinaryOperatorKind Op) {
    return Op == BO_And || Op == BO_Or || Op == BO_Xor || Op == BO_Shl ||
           Op == BO_Shr;
  }

  static bool isArithmeticOp(BinaryOperatorKind Op) {
    return Op == BO_Add || Op == BO_Sub || Op == BO_Mul || Op == BO_Div ||
           Op == BO_Rem;
  }

  static bool isCompoundOperandOp(BinaryOperatorKind Op) {
    return isBitwiseOrShiftOp(Op) || isArithmeticOp(Op);
  }

  static bool isExplicitlyParenthesized(const Expr *E) {
    if (!E)
      return false;
    return isa<ParenExpr>(E->IgnoreImpCasts());
  }

  static const BinaryOperator *getSemanticBinaryOperand(const Expr *E) {
    if (!E)
      return nullptr;
    return dyn_cast<BinaryOperator>(E->IgnoreParenImpCasts());
  }

  static bool hasUnparenthesizedCompoundOperand(const Expr *Operand) {
    if (!Operand || isExplicitlyParenthesized(Operand))
      return false;

    const BinaryOperator *OperandBO = getSemanticBinaryOperand(Operand);
    return OperandBO && isCompoundOperandOp(OperandBO->getOpcode());
  }

  static bool hasUnparenthesizedComparisonOperand(const Expr *Operand) {
    if (!Operand || isExplicitlyParenthesized(Operand))
      return false;

    const BinaryOperator *OperandBO = getSemanticBinaryOperand(Operand);
    return OperandBO && OperandBO->isComparisonOp();
  }

  void emitASTReport(const BinaryOperator *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getOperatorLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止比较表达式中的运算项未使用括号", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  class Visitor : public RecursiveASTVisitor<Visitor> {
    const GeneratedMisuseCompareExprChecker &Checker;
    AnalysisDeclContext *ADC;
    BugReporter &BR;

  public:
    Visitor(const GeneratedMisuseCompareExprChecker &Checker,
            AnalysisDeclContext *ADC, BugReporter &BR)
        : Checker(Checker), ADC(ADC), BR(BR) {}

    bool VisitBinaryOperator(BinaryOperator *BO) {
      if (!BO)
        return true;

      if (BO->isComparisonOp()) {
        if (hasUnparenthesizedCompoundOperand(BO->getLHS()) ||
            hasUnparenthesizedCompoundOperand(BO->getRHS()))
          Checker.emitASTReport(BO, ADC, BR);
        return true;
      }

      if (isBitwiseOrShiftOp(BO->getOpcode())) {
        if (hasUnparenthesizedComparisonOperand(BO->getLHS()) ||
            hasUnparenthesizedComparisonOperand(BO->getRHS()))
          Checker.emitASTReport(BO, ADC, BR);
      }

      return true;
    }
  };

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    Stmt *Body = ADC->getBody();
    if (!Body)
      return;

    Visitor V(*this, ADC, BR);
    V.TraverseStmt(Body);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedMisuseCompareExprChecker>(
      "gjb8114.MisuseCompareExpr",
      "禁止比较表达式中的运算项未使用括号");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;