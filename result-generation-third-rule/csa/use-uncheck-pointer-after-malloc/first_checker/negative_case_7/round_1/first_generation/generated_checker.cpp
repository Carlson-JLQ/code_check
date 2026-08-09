#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
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

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  struct PointerState {
    bool Allocated = false;
    bool Checked = false;
    bool Used = false;
    SourceLocation FirstViolationLoc;
    bool Reported = false;
  };

  static bool isNullPointerConstantExpr(const Expr *E) {
    if (!E)
      return false;

    E = E->IgnoreParenImpCasts();
    if (isa<CXXNullPtrLiteralExpr>(E))
      return true;

    if (const auto *IL = dyn_cast<IntegerLiteral>(E))
      return IL->getValue().isZero();

    return false;
  }

  static const Expr *stripParenCast(const Expr *E) {
    return E ? E->IgnoreParenImpCasts() : nullptr;
  }

  static const VarDecl *getBaseVarDecl(const Expr *E) {
    E = stripParenCast(E);
    if (!E)
      return nullptr;

    const auto *DRE = dyn_cast<DeclRefExpr>(E);
    if (!DRE)
      return nullptr;

    return dyn_cast<VarDecl>(DRE->getDecl());
  }

  static const VarDecl *getAssignedVarDecl(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return getBaseVarDecl(BO->getLHS());
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

  static bool isAllocationCallForVar(const Expr *RHS, const VarDecl *VD,
                                     bool IsReallocAssign) {
    const auto *CE = dyn_cast_or_null<CallExpr>(stripParenCast(RHS));
    if (!isAllocationCall(CE))
      return false;

    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;

    StringRef Name = FD->getName();
    if (Name == "realloc")
      return IsReallocAssign;
    return true;
  }

  static bool isSimpleNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
    Cond = stripParenCast(Cond);
    if (!Cond)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return getBaseVarDecl(UO->getSubExpr()) == VD;
      return false;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isEqualityOp())
        return false;

      const Expr *LHS = stripParenCast(BO->getLHS());
      const Expr *RHS = stripParenCast(BO->getRHS());
      bool LHSIsVar = getBaseVarDecl(LHS) == VD;
      bool RHSIsVar = getBaseVarDecl(RHS) == VD;
      bool LHSIsNull = isNullPointerConstantExpr(LHS);
      bool RHSIsNull = isNullPointerConstantExpr(RHS);

      return (LHSIsVar && RHSIsNull) || (RHSIsVar && LHSIsNull);
    }

    return getBaseVarDecl(Cond) == VD;
  }

  static bool isUseOfVar(const Expr *E, const VarDecl *VD) {
    E = stripParenCast(E);
    if (!E)
      return false;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return getBaseVarDecl(ASE->getBase()) == VD || getBaseVarDecl(ASE->getIdx()) == VD;

    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return getBaseVarDecl(ME->getBase()) == VD;

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->isIncrementDecrementOp() || UO->getOpcode() == UO_Deref ||
          UO->getOpcode() == UO_AddrOf || UO->getOpcode() == UO_Plus ||
          UO->getOpcode() == UO_Minus || UO->getOpcode() == UO_Not ||
          UO->getOpcode() == UO_LNot)
        return isUseOfVar(UO->getSubExpr(), VD);
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return isUseOfVar(BO->getLHS(), VD) || isUseOfVar(BO->getRHS(), VD);

    if (const auto *CO = dyn_cast<ConditionalOperator>(E))
      return isUseOfVar(CO->getCond(), VD) || isUseOfVar(CO->getTrueExpr(), VD) ||
             isUseOfVar(CO->getFalseExpr(), VD);

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isUseOfVar(Arg, VD))
          return true;
    }

    return false;
  }

  static bool isAllocationUse(const Expr *E, const VarDecl *VD) {
    E = stripParenCast(E);
    if (!E)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_Deref && isUseOfVar(UO->getSubExpr(), VD);

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return getBaseVarDecl(ASE->getBase()) == VD;

    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return getBaseVarDecl(ME->getBase()) == VD;

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isUseOfVar(Arg, VD))
          return true;
    }

    return isUseOfVar(E, VD);
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    if (!Violation || !ADC)
      return;

    const SourceManager &SM = BR.getSourceManager();
    SourceLocation Loc = Violation->getBeginLoc();
    if (Loc.isInvalid())
      return;

    PathDiagnosticLocation PLoc(Loc, SM);
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", PLoc);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void visitStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                 std::unordered_map<const VarDecl *, PointerState> &States,
                 std::unordered_set<const VarDecl *> &Reported) const {
    if (!S)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getAssignedVarDecl(S);
        if (VD) {
          const Expr *RHS = BO->getRHS();
          bool IsReallocAssign = isAllocationCallForVar(RHS, VD, true);
          bool IsAllocAssign = isAllocationCallForVar(RHS, VD, false);
          if (IsAllocAssign || IsReallocAssign) {
            PointerState &PS = States[VD];
            PS.Allocated = true;
            PS.Checked = false;
            PS.Used = false;
            if (!PS.Reported)
              PS.FirstViolationLoc = BO->getExprLoc();
          }
        }
      }
    }

    if (const auto *IF = dyn_cast<IfStmt>(S)) {
      const Stmt *Cond = IF->getCond();
      if (Cond) {
        for (auto &It : States) {
          const VarDecl *VD = It.first;
          PointerState &PS = It.second;
          if (PS.Allocated && !PS.Reported && isSimpleNullCheckCondition(Cond, VD))
            PS.Checked = true;
        }
      }
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(S)) {
      if (UO->getOpcode() == UO_Deref || UO->isIncrementDecrementOp()) {
        for (auto &It : States) {
          const VarDecl *VD = It.first;
          PointerState &PS = It.second;
          if (PS.Allocated && !PS.Checked && !PS.Reported &&
              isAllocationUse(UO, VD)) {
            PS.Reported = true;
            Reported.insert(VD);
            emitASTReport(UO, ADC, BR);
          }
        }
      }
    }

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(S)) {
      for (auto &It : States) {
        const VarDecl *VD = It.first;
        PointerState &PS = It.second;
        if (PS.Allocated && !PS.Checked && !PS.Reported &&
            getBaseVarDecl(ASE->getBase()) == VD) {
          PS.Reported = true;
          Reported.insert(VD);
          emitASTReport(ASE, ADC, BR);
        }
      }
    }

    if (const auto *ME = dyn_cast<MemberExpr>(S)) {
      for (auto &It : States) {
        const VarDecl *VD = It.first;
        PointerState &PS = It.second;
        if (PS.Allocated && !PS.Checked && !PS.Reported &&
            getBaseVarDecl(ME->getBase()) == VD) {
          PS.Reported = true;
          Reported.insert(VD);
          emitASTReport(ME, ADC, BR);
        }
      }
    }

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      for (const Expr *Arg : CE->arguments()) {
        for (auto &It : States) {
          const VarDecl *VD = It.first;
          PointerState &PS = It.second;
          if (PS.Allocated && !PS.Checked && !PS.Reported &&
              isUseOfVar(Arg, VD)) {
            PS.Reported = true;
            Reported.insert(VD);
            emitASTReport(Arg, ADC, BR);
          }
        }
      }
    }

    for (const Stmt *Child : S->children())
      visitStmt(Child, ADC, BR, States, Reported);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    std::unordered_map<const VarDecl *, PointerState> States;
    std::unordered_set<const VarDecl *> Reported;

    visitStmt(Body, ADC, BR, States, Reported);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;