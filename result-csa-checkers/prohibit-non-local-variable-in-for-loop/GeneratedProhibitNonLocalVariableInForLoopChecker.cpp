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
#include "llvm/Support/Casting.h"

using namespace clang;
using namespace ento;

namespace {
class GeneratedProhibitNonLocalVariableInForLoopChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "GJB8114 Prohibit non-local variable in for loop",
                   "GJB8114"};

  static bool isNonLocalVar(const VarDecl *VD) {
    if (!VD)
      return false;
    if (VD->isStaticLocal())
      return true;
    return VD->hasGlobalStorage();
  }

  const DeclRefExpr *findNonLocalVarRef(const Stmt *S) const {
    if (!S)
      return nullptr;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(S)) {
      const auto *VD = dyn_cast<VarDecl>(DRE->getDecl());
      if (isNonLocalVar(VD))
        return DRE;
      return nullptr;
    }

    for (const Stmt *Child : S->children()) {
      if (const DeclRefExpr *Found = findNonLocalVarRef(Child))
        return Found;
    }

    return nullptr;
  }

  void emitReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    PathDiagnosticLocation Loc(Violation->getBeginLoc(), BR.getSourceManager());
    auto R = std::make_unique<BasicBugReport>(
        BT, "禁止 for 循环控制变量使用非局部变量", Loc);
    R->addRange(Violation->getSourceRange());
    R->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(R));
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC,
                   BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *FS = dyn_cast<ForStmt>(S)) {
      const Stmt *Init = FS->getInit();
      if (!Init)
        return;

      if (isa<DeclStmt>(Init))
        return;

      const Expr *InitExpr = dyn_cast<Expr>(Init);
      if (!InitExpr)
        return;

      const DeclRefExpr *OffendingRef =
          findNonLocalVarRef(InitExpr->IgnoreParenImpCasts());
      if (OffendingRef)
        emitReport(OffendingRef, ADC, BR);

      return;
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
  Registry.addChecker<GeneratedProhibitNonLocalVariableInForLoopChecker>(
      "gjb8114.ProhibitNonLocalVariableInForLoop",
      "Prohibit non-local variables in for-loop control initialization");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;