#include <memory>
#include <optional>
#include <string>
#include <utility>

#include "clang/AST/Decl.h"
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

enum class PtrStateKind {
  None,
  AllocatedUnchecked,
  Checked
};

struct PtrState {
  PtrStateKind Kind = PtrStateKind::None;
  SourceLocation AllocLoc;
  SourceLocation FirstViolationLoc;
  bool Reported = false;
  bool EverUsed = false;
};

static bool isNullLiteralExpr(const Expr *E) {
  if (!E)
    return false;
  E = E->IgnoreParenImpCasts();
  return isa<CXXNullPtrLiteralExpr>(E) || (isa<IntegerLiteral>(E) &&
         E->getType()->isIntegerType() &&
         E->isNullPointerConstant(E->getASTContext(),
                                  Expr::NPC_ValueDependentIsNotNull));
}

static bool isPointerValueExpr(const Expr *E) {
  return E && E->IgnoreParenImpCasts()->getType()->isPointerType();
}

static bool isAllocationCall(const CallExpr *CE) {
  if (!CE)
    return false;
  const FunctionDecl *FD = CE->getDirectCallee();
  if (!FD)
    return false;
  IdentifierInfo *II = FD->getIdentifier();
  if (!II)
    return false;
  StringRef Name = II->getName();
  return Name == "malloc" || Name == "calloc" || Name == "realloc";
}

static bool isNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
  if (!Cond || !VD)
    return false;

  Cond = Cond->IgnoreParenImpCasts();

  if (const UnaryOperator *UO = dyn_cast<UnaryOperator>(Cond)) {
    if (UO->getOpcode() == UO_LNot) {
      const Expr *Sub = UO->getSubExpr()->IgnoreParenImpCasts();
      if (const DeclRefExpr *DRE = dyn_cast<DeclRefExpr>(Sub))
        return DRE->getDecl() == VD;
      return false;
    }
  }

  if (const DeclRefExpr *DRE = dyn_cast<DeclRefExpr>(Cond))
    return DRE->getDecl() == VD;

  if (const BinaryOperator *BO = dyn_cast<BinaryOperator>(Cond)) {
    if (!BO->isComparisonOp())
      return false;
    const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
    const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
    const DeclRefExpr *DRELHS = dyn_cast<DeclRefExpr>(LHS);
    const DeclRefExpr *DRERHS = dyn_cast<DeclRefExpr>(RHS);
    if (DRELHS && DRELHS->getDecl() == VD && isNullLiteralExpr(RHS))
      return true;
    if (DRERHS && DRERHS->getDecl() == VD && isNullLiteralExpr(LHS))
      return true;
  }

  return false;
}

class UseVisitor : public RecursiveASTVisitor<UseVisitor> {
  BugReporter &BR;
  AnalysisDeclContext *ADC;
  const SourceManager &SM;
  std::map<const VarDecl *, PtrState> &States;

  PtrState &stateFor(const VarDecl *VD) {
    return States[VD];
  }

  const VarDecl *getTrackedVar(const Expr *E) const {
    E = E->IgnoreParenImpCasts();
    if (const DeclRefExpr *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  void reportViolation(const VarDecl *VD, SourceLocation Loc) {
    if (!VD)
      return;
    PtrState &S = States[VD];
    if (S.Reported)
      return;
    S.Reported = true;
    S.FirstViolationLoc = Loc.isValid() ? Loc : S.AllocLoc;

    PathDiagnosticLocation PDL(S.FirstViolationLoc, SM);
    auto Report = std::make_unique<BasicBugReport>(
        BugType(VD->getASTContext().getSourceManager().getDiagnostics(),
                "Generated GJB8114 violation", "GJB8114"),
        "禁止动态分配的指针变量未检查即使用", PDL);
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void markUseIfViolation(const Expr *E) {
    const VarDecl *VD = getTrackedVar(E);
    if (!VD)
      return;
    auto It = States.find(VD);
    if (It == States.end())
      return;
    PtrState &S = It->second;
    if (S.Kind == PtrStateKind::AllocatedUnchecked && !S.Reported) {
      S.EverUsed = true;
      reportViolation(VD, E->getExprLoc());
    }
  }

public:
  UseVisitor(BugReporter &BR, AnalysisDeclContext *ADC,
             const SourceManager &SM, std::map<const VarDecl *, PtrState> &States)
      : BR(BR), ADC(ADC), SM(SM), States(States) {}

  bool VisitDeclStmt(DeclStmt *DS) {
    for (Decl *D : DS->decls()) {
      auto *VD = dyn_cast<VarDecl>(D);
      if (!VD)
        continue;
      const Expr *Init = VD->getInit();
      if (!Init)
        continue;
      Init = Init->IgnoreParenImpCasts();
      const CallExpr *CE = dyn_cast<CallExpr>(Init);
      if (!isAllocationCall(CE))
        continue;
      PtrState &S = stateFor(VD);
      S.Kind = PtrStateKind::AllocatedUnchecked;
      S.AllocLoc = VD->getLocation();
      S.Reported = false;
      S.EverUsed = false;
    }
    return true;
  }

  bool VisitBinaryOperator(BinaryOperator *BO) {
    if (!BO->isAssignmentOp())
      return true;
    const VarDecl *VD = getTrackedVar(BO->getLHS());
    if (!VD)
      return true;
    const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
    if (const CallExpr *CE = dyn_cast<CallExpr>(RHS)) {
      if (isAllocationCall(CE)) {
        PtrState &S = stateFor(VD);
        S.Kind = PtrStateKind::AllocatedUnchecked;
        S.AllocLoc = BO->getOperatorLoc();
        S.Reported = false;
        S.EverUsed = false;
        return true;
      }
    }
    return true;
  }

  bool VisitIfStmt(IfStmt *IS) {
    const Expr *Cond = IS->getCond();
    if (!Cond)
      return true;
    Cond = Cond->IgnoreParenImpCasts();
    const VarDecl *VD = nullptr;
    if (const DeclRefExpr *DRE = dyn_cast<DeclRefExpr>(Cond))
      VD = dyn_cast<VarDecl>(DRE->getDecl());
    else if (const UnaryOperator *UO = dyn_cast<UnaryOperator>(Cond))
      if (UO->getOpcode() == UO_LNot)
        VD = getTrackedVar(UO->getSubExpr());
    else if (const BinaryOperator *BO = dyn_cast<BinaryOperator>(Cond)) {
      const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
      if (const DeclRefExpr *DRELHS = dyn_cast<DeclRefExpr>(LHS))
        VD = dyn_cast<VarDecl>(DRELHS->getDecl());
      if (!VD)
        if (const DeclRefExpr *DRERHS = dyn_cast<DeclRefExpr>(RHS))
          VD = dyn_cast<VarDecl>(DRERHS->getDecl());
    }

    if (!VD)
      return true;

    auto It = States.find(VD);
    if (It == States.end())
      return true;

    if (isNullCheckCondition(Cond, VD) && It->second.Kind == PtrStateKind::AllocatedUnchecked) {
      It->second.Kind = PtrStateKind::Checked;
    }

    return true;
  }

  bool VisitUnaryOperator(UnaryOperator *UO) {
    if (UO->getOpcode() != UO_Deref)
      return true;
    markUseIfViolation(UO->getSubExpr());
    return true;
  }

  bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
    markUseIfViolation(ASE->getBase());
    markUseIfViolation(ASE->getIdx());
    return true;
  }

  bool VisitMemberExpr(MemberExpr *ME) {
    markUseIfViolation(ME->getBase());
    return true;
  }

  bool VisitCallExpr(CallExpr *CE) {
    for (const Expr *Arg : CE->arguments())
      markUseIfViolation(Arg);
    return true;
  }

  bool VisitReturnStmt(ReturnStmt *RS) {
    markUseIfViolation(RS->getRetValue());
    return true;
  }
};

class GeneratedUseUncheckPointerAfterMallocChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *ACD = AM.getAnalysisDeclContext(D);
    if (!ACD)
      return;

    const Stmt *Body = ACD->getBody();
    if (!Body)
      return;

    std::map<const VarDecl *, PtrState> States;
    UseVisitor V(BR, const_cast<AnalysisDeclContext *>(ACD),
                 AM.getSourceManager(), States);
    V.TraverseStmt(const_cast<Stmt *>(Body));
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;