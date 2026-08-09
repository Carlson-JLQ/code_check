#include <map>
#include <memory>
#include <optional>
#include <string>
#include <utility>

#include "clang/AST/ASTContext.h"
#include "clang/AST/ASTTypeTraits.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ExprCXX.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Type.h"
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

  struct VarState {
    bool Allocated = false;
    bool CheckedSinceAlloc = false;
    bool Violated = false;
    const Expr *FirstUse = nullptr;
  };

  static const Expr *ignoreCasts(const Expr *E) {
    while (E) {
      E = E->IgnoreParenImpCasts();
      if (const auto *MTE = dyn_cast<MaterializeTemporaryExpr>(E))
        E = MTE->getSubExpr();
      else
        break;
    }
    return E;
  }

  static bool isNullLiteralOrMacro(const Expr *E) {
    E = ignoreCasts(E);
    if (!E)
      return false;
    return isa<CXXNullPtrLiteralExpr>(E) ||
           E->isNullPointerConstant(E->getExprLoc(),
                                    Expr::NPC_ValueDependentIsNotNull);
  }

  static bool isAllocationCall(const Expr *E) {
    E = ignoreCasts(E);
    const auto *CE = dyn_cast_or_null<CallExpr>(E);
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static bool isPointerLike(const VarDecl *VD) {
    return VD && VD->getType()->isPointerType();
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    E = ignoreCasts(E);
    if (!E)
      return nullptr;
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static const VarDecl *getAssignedVar(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return getReferencedVar(BO->getLHS());
  }

  static bool exprUsesVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = ignoreCasts(E);
    if (!E)
      return false;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;

    for (const Stmt *Child : E->children()) {
      if (const auto *CE = dyn_cast_or_null<Expr>(Child)) {
        if (exprUsesVar(CE, VD))
          return true;
      }
    }
    return false;
  }

  static bool isNullCheckCondition(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;

    E = ignoreCasts(E);
    if (!E)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_LNot)
        return exprUsesVar(UO->getSubExpr(), VD);
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;
      const Expr *L = ignoreCasts(BO->getLHS());
      const Expr *R = ignoreCasts(BO->getRHS());
      return (exprUsesVar(L, VD) && isNullLiteralOrMacro(R)) ||
             (exprUsesVar(R, VD) && isNullLiteralOrMacro(L));
    }

    return exprUsesVar(E, VD);
  }

  static const Stmt *getBodyStmt(const Decl *D) {
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      return FD->getBody();
    return nullptr;
  }

  void emitASTReport(const Expr *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    SourceLocation Loc = Violation->getExprLoc();
    PathDiagnosticLocation PLoc(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", PLoc);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void analyzeStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                   std::map<const VarDecl *, VarState> &States,
                   bool InCondition) const {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      if (const Expr *Cond = IfS->getCond()) {
        analyzeStmt(Cond, ADC, BR, States, true);
        if (const auto *VD = getReferencedVar(Cond)) {
          if (isNullCheckCondition(Cond, VD) && States.count(VD) &&
              States[VD].Allocated)
            States[VD].CheckedSinceAlloc = true;
        }
      }
      if (const Stmt *Then = IfS->getThen())
        analyzeStmt(Then, ADC, BR, States, false);
      if (const Stmt *Else = IfS->getElse())
        analyzeStmt(Else, ADC, BR, States, false);
      return;
    }

    if (const auto *WhileS = dyn_cast<WhileStmt>(S)) {
      if (const Expr *Cond = WhileS->getCond()) {
        analyzeStmt(Cond, ADC, BR, States, true);
        if (const auto *VD = getReferencedVar(Cond)) {
          if (isNullCheckCondition(Cond, VD) && States.count(VD) &&
              States[VD].Allocated)
            States[VD].CheckedSinceAlloc = true;
        }
      }
      if (const Stmt *Body = WhileS->getBody())
        analyzeStmt(Body, ADC, BR, States, false);
      return;
    }

    if (const auto *ForS = dyn_cast<ForStmt>(S)) {
      if (const Stmt *Init = ForS->getInit())
        analyzeStmt(Init, ADC, BR, States, false);
      if (const Expr *Cond = ForS->getCond()) {
        analyzeStmt(Cond, ADC, BR, States, true);
        if (const auto *VD = getReferencedVar(Cond)) {
          if (isNullCheckCondition(Cond, VD) && States.count(VD) &&
              States[VD].Allocated)
            States[VD].CheckedSinceAlloc = true;
        }
      }
      if (const Stmt *Body = ForS->getBody())
        analyzeStmt(Body, ADC, BR, States, false);
      if (const Stmt *Inc = ForS->getInc())
        analyzeStmt(Inc, ADC, BR, States, false);
      return;
    }

    if (const auto *DoS = dyn_cast<DoStmt>(S)) {
      if (const Stmt *Body = DoS->getBody())
        analyzeStmt(Body, ADC, BR, States, false);
      if (const Expr *Cond = DoS->getCond()) {
        analyzeStmt(Cond, ADC, BR, States, true);
        if (const auto *VD = getReferencedVar(Cond)) {
          if (isNullCheckCondition(Cond, VD) && States.count(VD) &&
              States[VD].Allocated)
            States[VD].CheckedSinceAlloc = true;
        }
      }
      return;
    }

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!isPointerLike(VD))
          continue;
        if (const Expr *Init = VD->getInit()) {
          if (isAllocationCall(Init)) {
            VarState &St = States[VD];
            St.Allocated = true;
            St.CheckedSinceAlloc = false;
            St.Violated = false;
            St.FirstUse = nullptr;
          }
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getAssignedVar(S);
        if (VD && isPointerLike(VD) && isAllocationCall(BO->getRHS())) {
          VarState &St = States[VD];
          St.Allocated = true;
          St.CheckedSinceAlloc = false;
          St.Violated = false;
          St.FirstUse = nullptr;
        }
      }
    }

    if (const auto *E = dyn_cast<Expr>(S)) {
      if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
        if (UO->getOpcode() == UO_Deref || UO->getOpcode() == UO_AddrOf) {
          const VarDecl *VD = getReferencedVar(UO->getSubExpr());
          if (VD && States.count(VD) && States[VD].Allocated &&
              !States[VD].CheckedSinceAlloc && !States[VD].Violated) {
            States[VD].Violated = true;
            States[VD].FirstUse = E;
            emitASTReport(E, ADC, BR);
          }
        }
      } else if (const auto *CE = dyn_cast<CallExpr>(E)) {
        for (const Expr *Arg : CE->arguments()) {
          const VarDecl *VD = getReferencedVar(Arg);
          if (VD && States.count(VD) && States[VD].Allocated &&
              !States[VD].CheckedSinceAlloc && !States[VD].Violated) {
            States[VD].Violated = true;
            States[VD].FirstUse = Arg;
            emitASTReport(Arg, ADC, BR);
          }
        }
      } else if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E)) {
        const VarDecl *VD = getReferencedVar(ASE->getBase());
        if (VD && States.count(VD) && States[VD].Allocated &&
            !States[VD].CheckedSinceAlloc && !States[VD].Violated) {
          States[VD].Violated = true;
          States[VD].FirstUse = E;
          emitASTReport(E, ADC, BR);
        }
      }
    }

    for (const Stmt *Child : S->children()) {
      if (const auto *ChildStmt = dyn_cast_or_null<Stmt>(Child))
        analyzeStmt(ChildStmt, ADC, BR, States, InCondition);
    }
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const Stmt *Body = getBodyStmt(D);
    if (!Body)
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    std::map<const VarDecl *, VarState> States;
    analyzeStmt(Body, ADC, BR, States, false);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;