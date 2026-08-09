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
class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static bool isNullCheckExpr(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_LNot;
    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;
      const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
      return (isa<CXXNullPtrLiteralExpr>(LHS) || isa<IntegerLiteral>(LHS) ||
              isa<CXXNullPtrLiteralExpr>(RHS) || isa<IntegerLiteral>(RHS) ||
              isa<GNUNullExpr>(LHS) || isa<GNUNullExpr>(RHS));
    }
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E) ||
           isa<IntegerLiteral>(E);
  }

  static bool isPointerUseExpr(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();

    if (isa<DeclRefExpr>(E) || isa<MemberExpr>(E) || isa<ArraySubscriptExpr>(E) ||
        isa<UnaryOperator>(E) || isa<CallExpr>(E))
      return true;

    return false;
  }

  static bool containsUseOrCheck(const Stmt *S, const VarDecl *VD,
                                 bool &SawCheck, const Stmt *&FirstUse,
                                 const Stmt *&FirstCheck) {
    if (!S)
      return false;

    if (const auto *E = dyn_cast<Expr>(S)) {
      const Expr *Ex = E->IgnoreParenImpCasts();
      if (const auto *DRE = dyn_cast<DeclRefExpr>(Ex)) {
        if (DRE->getDecl() == VD) {
          FirstUse = FirstUse ? FirstUse : S;
          return true;
        }
      }
      if (const auto *ME = dyn_cast<MemberExpr>(Ex)) {
        if (ME->getBase()->IgnoreParenImpCasts()) {
          const Expr *Base = ME->getBase()->IgnoreParenImpCasts();
          if (const auto *DRE = dyn_cast<DeclRefExpr>(Base)) {
            if (DRE->getDecl() == VD) {
              FirstUse = FirstUse ? FirstUse : S;
              return true;
            }
          }
        }
      }
      if (isNullCheckExpr(Ex)) {
        if (const auto *BO = dyn_cast<BinaryOperator>(Ex)) {
          const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
          const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
          if ((isa<DeclRefExpr>(LHS) && cast<DeclRefExpr>(LHS)->getDecl() == VD) ||
              (isa<DeclRefExpr>(RHS) && cast<DeclRefExpr>(RHS)->getDecl() == VD)) {
            SawCheck = true;
            FirstCheck = FirstCheck ? FirstCheck : S;
          }
        } else if (const auto *UO = dyn_cast<UnaryOperator>(Ex)) {
          const Expr *Sub = UO->getSubExpr()->IgnoreParenImpCasts();
          if (isa<DeclRefExpr>(Sub) && cast<DeclRefExpr>(Sub)->getDecl() == VD) {
            SawCheck = true;
            FirstCheck = FirstCheck ? FirstCheck : S;
          }
        }
      }
    }

    for (const Stmt *Child : S->children()) {
      if (containsUseOrCheck(Child, VD, SawCheck, FirstUse, FirstCheck))
        return true;
    }
    return false;
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void checkStatementForVar(const Stmt *S, const VarDecl *VD,
                            AnalysisDeclContext *ADC, BugReporter &BR) const {
    bool SawCheck = false;
    const Stmt *FirstUse = nullptr;
    const Stmt *FirstCheck = nullptr;
    containsUseOrCheck(S, VD, SawCheck, FirstUse, FirstCheck);

    if (FirstUse && (!SawCheck || (FirstCheck && FirstUse->getBeginLoc().isValid() &&
                                   FirstCheck->getBeginLoc().isValid() &&
                                   FirstUse->getBeginLoc() < FirstCheck->getBeginLoc()))) {
      emitASTReport(FirstUse, ADC, BR);
    }
  }

  void scanStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;
        const Expr *Init = VD->getInit();
        if (!Init)
          continue;
        const Expr *Clean = Init->IgnoreParenImpCasts();
        if (const auto *CE = dyn_cast<CallExpr>(Clean)) {
          const FunctionDecl *FD = CE->getDirectCallee();
          if (!FD)
            continue;
          StringRef Name = FD->getName();
          bool IsAlloc = Name == "malloc" || Name == "calloc" || Name == "realloc";
          if (!IsAlloc)
            continue;
          const Stmt *UseOrCheck = S->getStmtClass() == Stmt::DeclStmtClass ? S : Init;
          checkStatementForVar(UseOrCheck, VD, ADC, BR);
        }
      }
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *ACD = dyn_cast<FunctionDecl>(D);
    if (!ACD)
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    const Stmt *Body = ACD->getBody();
    if (!Body || !ADC)
      return;

    scanStmt(Body, ADC, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;