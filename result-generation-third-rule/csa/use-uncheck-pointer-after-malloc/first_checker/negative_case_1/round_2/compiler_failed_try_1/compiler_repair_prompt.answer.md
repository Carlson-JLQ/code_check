I’m patching the checker to remove the unsupported Clang API call and keep the registration, class name, and diagnostic shape intact. Then I’ll do a quick readback for compile-facing issues before I hand back the implementation.I found the failure point: the null-constant helper is using `Expr::getExprClass()`, which is not available in this Clang build. I’m narrowing that helper to public AST forms only, so the checker stays self-contained and compiles against the local headers.```cpp
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "clang/AST/AST.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/Basic/SourceLocation.h"
#include "clang/Basic/SourceManager.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

struct VarUseState {
  enum class Kind { Unknown, Allocated, Checked, Reported };

  Kind State = Kind::Unknown;
  SourceLocation AllocLoc;
  SourceLocation FirstViolationLoc;
};

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static bool isNullConstant(const Expr *E) {
    if (!E)
      return false;

    E = E->IgnoreParenImpCasts();

    if (isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E))
      return true;

    if (const auto *IL = dyn_cast<IntegerLiteral>(E))
      return IL->getValue().isZero();

    return false;
  }

  static const DeclRefExpr *getDirectDeclRef(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    return dyn_cast<DeclRefExpr>(E);
  }

  static const VarDecl *getTrackedVar(const Expr *E) {
    const auto *DRE = getDirectDeclRef(E);
    if (!DRE)
      return nullptr;
    return dyn_cast<VarDecl>(DRE->getDecl());
  }

  static bool isAllocationCall(const CallExpr *CE) {
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const Expr *getAssignedRHS(const BinaryOperator *BO) {
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return BO->getRHS();
  }

  static const VarDecl *getAssignedVar(const BinaryOperator *BO) {
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return getTrackedVar(BO->getLHS());
  }

  static bool isNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
    if (!Cond || !VD)
      return false;
    Cond = Cond->IgnoreParenImpCasts();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return cast<VarDecl>(DRE->getDecl()) == VD;

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return isNullCheckCondition(UO->getSubExpr(), VD);
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isRelationalOp() && !BO->isEqualityOp())
        return false;
      const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
      return (getTrackedVar(L) == VD && isNullConstant(R)) ||
             (getTrackedVar(R) == VD && isNullConstant(L));
    }

    return false;
  }

  static bool isUseExpression(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return cast<VarDecl>(DRE->getDecl()) == VD;

    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return isUseExpression(UO->getSubExpr(), VD);

    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return isUseExpression(BO->getLHS(), VD) ||
             isUseExpression(BO->getRHS(), VD);

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isUseExpression(Arg, VD))
          return true;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return isUseExpression(ME->getBase(), VD);

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return isUseExpression(ASE->getBase(), VD) ||
             isUseExpression(ASE->getIdx(), VD);

    if (const auto *CO = dyn_cast<CastExpr>(E))
      return isUseExpression(CO->getSubExpr(), VD);

    return false;
  }

  static const Expr *getConditionExpr(const Stmt *S) {
    if (const auto *IS = dyn_cast<IfStmt>(S))
      return IS->getCond();
    if (const auto *WS = dyn_cast<WhileStmt>(S))
      return WS->getCond();
    if (const auto *DS = dyn_cast<DoStmt>(S))
      return DS->getCond();
    if (const auto *FS = dyn_cast<ForStmt>(S))
      return FS->getCond();
    return nullptr;
  }

  static const Expr *getInitExpr(const VarDecl *VD) {
    if (!VD)
      return nullptr;
    return dyn_cast_or_null<Expr>(VD->getInit());
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    SourceLocation Loc = Violation ? Violation->getBeginLoc() : SourceLocation();
    PathDiagnosticLocation Location(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    if (Violation)
      Report->addRange(Violation->getSourceRange());
    if (ADC)
      Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void analyzeStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                   std::unordered_map<const VarDecl *, VarUseState> &States,
                   std::unordered_set<const VarDecl *> &Reported) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !VD->getType()->isPointerType())
          continue;
        const Expr *Init = getInitExpr(VD);
        if (!Init)
          continue;
        Init = Init->IgnoreParenImpCasts();
        const auto *CE = dyn_cast<CallExpr>(Init);
        if (CE && isAllocationCall(CE)) {
          auto &St = States[VD];
          St.State = VarUseState::Kind::Allocated;
          St.AllocLoc = VD->getLocation();
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      const VarDecl *Assigned = getAssignedVar(BO);
      const Expr *RHS = getAssignedRHS(BO);
      if (Assigned && Assigned->getType()->isPointerType() && RHS) {
        RHS = RHS->IgnoreParenImpCasts();
        const auto *CE = dyn_cast<CallExpr>(RHS);
        if (CE && isAllocationCall(CE)) {
          auto &St = States[Assigned];
          St.State = VarUseState::Kind::Allocated;
          St.AllocLoc = BO->getOperatorLoc();
        }
      }
    }

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      const FunctionDecl *FD = CE->getDirectCallee();
      if (FD && FD->getName() == "realloc" && CE->getNumArgs() >= 1) {
        if (const VarDecl *VD = getTrackedVar(CE->getArg(0))) {
          if (VD->getType()->isPointerType()) {
            auto &St = States[VD];
            St.State = VarUseState::Kind::Allocated;
            St.AllocLoc = CE->getBeginLoc();
          }
        }
      }
    }

    if (const Expr *Cond = getConditionExpr(S)) {
      for (auto &[VD, St] : States) {
        if (St.State == VarUseState::Kind::Allocated &&
            isNullCheckCondition(Cond, VD)) {
          St.State = VarUseState::Kind::Checked;
        }
      }
    }

    for (auto &[VD, St] : States) {
      if (Reported.count(VD))
        continue;
      if (St.State != VarUseState::Kind::Allocated)
        continue;

      if (isUseExpression(dyn_cast_or_null<Expr>(S), VD)) {
        St.FirstViolationLoc = S->getBeginLoc();
        St.State = VarUseState::Kind::Reported;
        Reported.insert(VD);
        emitASTReport(S, ADC, BR);
        continue;
      }

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *D : DS->decls()) {
          const auto *VDUse = dyn_cast<VarDecl>(D);
          if (!VDUse || VDUse != VD)
            continue;
          const Expr *Init = getInitExpr(VDUse);
          if (Init && isUseExpression(Init, VD)) {
            St.FirstViolationLoc = Init->getBeginLoc();
            St.State = VarUseState::Kind::Reported;
            Reported.insert(VD);
            emitASTReport(Init, ADC, BR);
          }
        }
      }
    }

    for (const Stmt *Child : S->children())
      analyzeStmt(Child, ADC, BR, States, Reported);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    std::unordered_map<const VarDecl *, VarUseState> States;
    std::unordered_set<const VarDecl *> Reported;

    analyzeStmt(Body, AM.getAnalysisDeclContext(D), BR, States, Reported);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
```