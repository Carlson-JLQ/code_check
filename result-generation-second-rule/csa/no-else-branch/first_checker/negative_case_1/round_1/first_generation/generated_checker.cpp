#include <memory>

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
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static const IfStmt *findTopLevelIfChain(const Stmt *S) {
    const auto *If = dyn_cast_or_null<IfStmt>(S);
    if (!If)
      return nullptr;

    const IfStmt *Top = If;
    while (const auto *Parent = dyn_cast_or_null<IfStmt>(Top->getParentIf())) {
      Top = Parent;
    }
    return Top;
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止省略 if-else if 语句的 else 分支", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void checkStmtForMissingElse(const Stmt *S, AnalysisDeclContext *ADC,
                               BugReporter &BR) const {
    const auto *If = dyn_cast_or_null<IfStmt>(S);
    if (!If)
      return;

    const IfStmt *ChainHead = findTopLevelIfChain(If);
    if (!ChainHead)
      return;

    const IfStmt *Current = ChainHead;
    bool HasElseIf = false;
    while (Current) {
      const Stmt *Else = Current->getElse();
      if (!Else) {
        if (HasElseIf)
          emitASTReport(Current, ADC, BR);
        return;
      }

      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        return;

      HasElseIf = true;
      Current = ElseIf;
    }
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *ACD = AM.getAnalysisDeclContext(D);
    if (!ACD)
      return;

    const Stmt *Body = D->getBody();
    if (!Body)
      return;

    for (const Stmt *Child : Body->children()) {
      if (!Child)
        continue;

      if (const auto *If = dyn_cast<IfStmt>(Child)) {
        checkStmtForMissingElse(If, ACD, BR);
      }

      for (const Stmt *Sub : Child->children()) {
        if (const auto *SubIf = dyn_cast_or_null<IfStmt>(Sub))
          checkStmtForMissingElse(SubIf, ACD, BR);
      }
    }

    if (const auto *Compound = dyn_cast<CompoundStmt>(Body)) {
      for (const Stmt *Child : Compound->body()) {
        if (const auto *If = dyn_cast<IfStmt>(Child))
          checkStmtForMissingElse(If, ACD, BR);
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