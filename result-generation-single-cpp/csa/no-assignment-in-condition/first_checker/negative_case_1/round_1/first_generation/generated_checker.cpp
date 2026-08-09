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
const BinaryOperator *findAssignment(const Stmt *S) {
  if (!S)
    return nullptr;

  if (const auto *B = dyn_cast<BinaryOperator>(S)) {
    if (B->isAssignmentOp())
      return B;
  }

  for (const Stmt *Child : S->children()) {
    if (const BinaryOperator *Found = findAssignment(Child))
      return Found;
  }

  return nullptr;
}

class GeneratedNoAssignmentInConditionChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "禁止将赋值语句作为逻辑表达式", "GJB8114"};

  void inspectCondition(const Expr *Condition, AnalysisDeclContext *ADC,
                        BugReporter &BR) const {
    const BinaryOperator *Assignment = findAssignment(Condition);
    if (!Assignment)
      return;

    PathDiagnosticLocation Location(Assignment->getExprLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止将赋值语句作为逻辑表达式 [gjb8114-r-1-6-3]", Location);
    Report->addRange(Assignment->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void inspectStatements(const Stmt *S, AnalysisDeclContext *ADC,
                         BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S))
      inspectCondition(If->getCond(), ADC, BR);
    else if (const auto *While = dyn_cast<WhileStmt>(S))
      inspectCondition(While->getCond(), ADC, BR);
    else if (const auto *Do = dyn_cast<DoStmt>(S))
      inspectCondition(Do->getCond(), ADC, BR);
    else if (const auto *For = dyn_cast<ForStmt>(S))
      inspectCondition(For->getCond(), ADC, BR);

    for (const Stmt *Child : S->children())
      inspectStatements(Child, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    inspectStatements(D->getBody(), ADC, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoAssignmentInConditionChecker>(
      "gjb8114.NoAssignmentInCondition",
      "Detect assignment operations in branch conditions");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;