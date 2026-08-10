#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {
class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "NoElseBranch", "gjb8114-r-1-4-1"};

  void emitReport(const IfStmt *Violation, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    if (!Violation || !ADC)
      return;

    PathDiagnosticLocation Loc(Violation->getIfLoc(), BR.getSourceManager());
    auto R = std::make_unique<BasicBugReport>(
        BT, "禁止省略 if-else if 语句的 else 分支 [gjb8114-r-1-4-1]", Loc);
    R->addRange(Violation->getSourceRange());
    R->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(R));
  }

  const IfStmt *getTerminalElseIf(const IfStmt *Head) const {
    const IfStmt *Current = Head;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const auto *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      Current = ElseIf;
    }
    return Current;
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                   bool InElseIfChain = false) const {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      const Stmt *Else = IS->getElse();
      const auto *ElseIf = dyn_cast_or_null<IfStmt>(Else);

      if (!InElseIfChain && ElseIf) {
        const IfStmt *Terminal = getTerminalElseIf(IS);
        if (Terminal && Terminal->getElse() == nullptr)
          emitReport(Terminal, ADC, BR);
      }

      inspectStmt(IS->getThen(), ADC, BR, false);

      if (ElseIf)
        inspectStmt(ElseIf, ADC, BR, true);
      else
        inspectStmt(Else, ADC, BR, false);

      return;
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, ADC, BR, false);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = ADC->getBody();
    if (!Body)
      return;

    inspectStmt(Body, const_cast<AnalysisDeclContext *>(ADC), BR, false);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114.NoElseBranch",
                                                    "NoElseBranch checker");
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114-r-1-4-1",
                                                    "NoElseBranch checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;