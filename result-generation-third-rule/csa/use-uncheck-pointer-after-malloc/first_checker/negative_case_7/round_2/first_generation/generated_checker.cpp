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

using namespace clang;
using namespace ento;

namespace {

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  struct VarInfo {
    const VarDecl *VD = nullptr;
    bool IsDynamic = false;
    bool CheckedSinceAlloc = false;
    bool UsedSinceAlloc = false;
    bool Reported = false;
    const Expr *LastAllocExpr = nullptr;
    SourceLocation LastUseLoc;
  };

  struct CallInfo {
    const FunctionDecl *FD = nullptr;
    const Expr *CalleeExpr = nullptr;
    SmallVector<const Expr *, 4> Args;
  };

  static const Expr *ignoreParenImpCasts(const Expr *E) {
    if (!E)
      return nullptr;
    return E->IgnoreParenParenCasts();
  }

  static const Expr *stripExpr(const Stmt *S) {
    return dyn_cast_or_null<Expr>(S);
  }

  static bool isNullPointerConstantExpr(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return E->isNullPointerConstant(E->getExprLoc(),
                                    Expr::NPC_ValueDependentIsNotNull);
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return dyn_cast<VarDecl>(ME->getMemberDecl());
    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_Deref)
        return getReferencedVar(UO->getSubExpr());
    }
    return nullptr;
  }

  static bool isAllocationFunctionName(StringRef Name) {
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const FunctionDecl *getDirectCallee(const Expr *E) {
    if (!E)
      return nullptr;
    if (const auto *CE = dyn_cast<CallExpr>(E->IgnoreParenImpCasts()))
      return CE->getDirectCallee();
    return nullptr;
  }

  static const Expr *getInitializerExpr(const VarDecl *VD) {
    if (!VD)
      return nullptr;
    return VD->getInit();
  }

  static bool isCheckedConditionForVar(const Expr *Cond, const VarDecl *VD) {
    if (!Cond || !VD)
      return false;

    Cond = Cond->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return isCheckedConditionForVar(UO->getSubExpr(), VD);
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isComparisonOp())
        return false;
      const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
      const VarDecl *LV = getReferencedVar(L);
      const VarDecl *RV = getReferencedVar(R);
      if (LV == VD && isNullPointerConstantExpr(R))
        return true;
      if (RV == VD && isNullPointerConstantExpr(L))
        return true;
      return false;
    }

    return getReferencedVar(Cond) == VD;
  }

  static bool isAllocationCall(const Expr *E) {
    const FunctionDecl *FD = getDirectCallee(E);
    if (!FD)
      return false;
    return isAllocationFunctionName(FD->getName());
  }

  static const Expr *getAssignmentRHS(const Expr *E) {
    if (const auto *BO = dyn_cast_or_null<BinaryOperator>(E)) {
      if (BO->isAssignmentOp())
        return BO->getRHS();
    }
    if (const auto *UO = dyn_cast_or_null<UnaryOperator>(E)) {
      (void)UO;
    }
    return nullptr;
  }

  void report(const VarInfo &VI, AnalysisDeclContext *ADC,
              BugReporter &BR) const {
    if (!VI.VD || VI.Reported)
      return;

    SourceLocation Loc = VI.LastUseLoc.isValid()
                             ? VI.LastUseLoc
                             : VI.LastAllocExpr ? VI.LastAllocExpr->getBeginLoc()
                                                : VI.VD->getLocation();

    PathDiagnosticLocation PDL(Loc, BR.getSourceManager());
    auto R = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", PDL);
    if (VI.LastUseLoc.isValid())
      R->addRange(SourceRange(VI.LastUseLoc, VI.LastUseLoc));
    else if (VI.LastAllocExpr)
      R->addRange(VI.LastAllocExpr->getSourceRange());
    R->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(R));
  }

  void scanExprForUses(const Expr *E, llvm::DenseMap<const VarDecl *, VarInfo> &Vars,
                       AnalysisDeclContext *ADC, BugReporter &BR,
                       bool InCondition = false) const {
    if (!E)
      return;

    E = E->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_LNot) {
        const Expr *Sub = UO->getSubExpr();
        if (const VarDecl *VD = getReferencedVar(Sub)) {
          auto It = Vars.find(VD);
          if (It != Vars.end() && It->second.IsDynamic) {
            It->second.CheckedSinceAlloc = true;
            return;
          }
        }
        scanExprForUses(Sub, Vars, ADC, BR, true);
        return;
      }
      scanExprForUses(UO->getSubExpr(), Vars, ADC, BR, InCondition);
      return;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (BO->isComparisonOp()) {
        const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
        const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
        if (const VarDecl *VD = getReferencedVar(L)) {
          auto It = Vars.find(VD);
          if (It != Vars.end() && It->second.IsDynamic &&
              isNullPointerConstantExpr(R)) {
            It->second.CheckedSinceAlloc = true;
            return;
          }
        }
        if (const VarDecl *VD = getReferencedVar(R)) {
          auto It = Vars.find(VD);
          if (It != Vars.end() && It->second.IsDynamic &&
              isNullPointerConstantExpr(L)) {
            It->second.CheckedSinceAlloc = true;
            return;
          }
        }
      }
      scanExprForUses(BO->getLHS(), Vars, ADC, BR, InCondition);
      scanExprForUses(BO->getRHS(), Vars, ADC, BR, InCondition);
      return;
    }

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        scanExprForUses(Arg, Vars, ADC, BR, InCondition);
      return;
    }

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E)) {
      const VarDecl *Base = getReferencedVar(ASE->getBase());
      if (Base) {
        auto It = Vars.find(Base);
        if (It != Vars.end() && It->second.IsDynamic) {
          It->second.UsedSinceAlloc = true;
          It->second.LastUseLoc = ASE->getExprLoc();
          if (!It->second.CheckedSinceAlloc && !It->second.Reported) {
            report(It->second, ADC, BR);
            It->second.Reported = true;
          }
        }
      }
      scanExprForUses(ASE->getBase(), Vars, ADC, BR, InCondition);
      scanExprForUses(ASE->getIdx(), Vars, ADC, BR, InCondition);
      return;
    }

    if (const VarDecl *VD = getReferencedVar(E)) {
      auto It = Vars.find(VD);
      if (It != Vars.end() && It->second.IsDynamic) {
        if (!InCondition) {
          It->second.UsedSinceAlloc = true;
          It->second.LastUseLoc = E->getExprLoc();
          if (!It->second.CheckedSinceAlloc && !It->second.Reported) {
            report(It->second, ADC, BR);
            It->second.Reported = true;
          }
        }
      }
      return;
    }

    for (const Stmt *Child : E->children()) {
      if (const Expr *CE = dyn_cast_or_null<Expr>(Child))
        scanExprForUses(CE, Vars, ADC, BR, InCondition);
    }
  }

  void processStmt(const Stmt *S, llvm::DenseMap<const VarDecl *, VarInfo> &Vars,
                   AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;
        VarInfo &VI = Vars[VD];
        VI.VD = VD;
        if (const Expr *Init = getInitializerExpr(VD)) {
          scanExprForUses(Init, Vars, ADC, BR);
          if (isAllocationCall(Init)) {
            VI.IsDynamic = true;
            VI.CheckedSinceAlloc = false;
            VI.UsedSinceAlloc = false;
            VI.Reported = false;
            VI.LastAllocExpr = Init;
          }
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getReferencedVar(BO->getLHS());
        const Expr *RHS = BO->getRHS();
        scanExprForUses(RHS, Vars, ADC, BR);
        if (VD) {
          auto &VI = Vars[VD];
          VI.VD = VD;
          if (isAllocationCall(RHS)) {
            VI.IsDynamic = true;
            VI.CheckedSinceAlloc = false;
            VI.UsedSinceAlloc = false;
            VI.Reported = false;
            VI.LastAllocExpr = RHS;
          } else {
            if (VI.IsDynamic) {
              VI.CheckedSinceAlloc = false;
              VI.UsedSinceAlloc = false;
              VI.Reported = false;
            }
          }
          return;
        }
      }
      scanExprForUses(BO->getLHS(), Vars, ADC, BR);
      scanExprForUses(BO->getRHS(), Vars, ADC, BR);
      return;
    }

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      scanExprForUses(IS->getCond(), Vars, ADC, BR, true);
      for (const Stmt *Child : IS->children()) {
        if (Child != IS->getCond())
          processStmt(Child, Vars, ADC, BR);
      }
      return;
    }

    if (const auto *WS = dyn_cast<WhileStmt>(S)) {
      scanExprForUses(WS->getCond(), Vars, ADC, BR, true);
      processStmt(WS->getBody(), Vars, ADC, BR);
      return;
    }

    if (const auto *FS = dyn_cast<ForStmt>(S)) {
      if (const Stmt *Init = FS->getInit())
        processStmt(Init, Vars, ADC, BR);
      scanExprForUses(FS->getCond(), Vars, ADC, BR, true);
      if (const Stmt *Inc = FS->getInc())
        processStmt(Inc, Vars, ADC, BR);
      processStmt(FS->getBody(), Vars, ADC, BR);
      return;
    }

    if (const auto *RS = dyn_cast<ReturnStmt>(S)) {
      scanExprForUses(RS->getRetValue(), Vars, ADC, BR);
      return;
    }

    if (const auto *E = dyn_cast<Expr>(S)) {
      scanExprForUses(E, Vars, ADC, BR);
      return;
    }

    for (const Stmt *Child : S->children())
      processStmt(Child, Vars, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    llvm::DenseMap<const VarDecl *, VarInfo> Vars;
    processStmt(FD->getBody(), Vars, ADC, BR);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc",
      "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;