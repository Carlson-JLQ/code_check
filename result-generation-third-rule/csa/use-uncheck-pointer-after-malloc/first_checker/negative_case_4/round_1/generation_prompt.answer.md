I’m checking the repo layout and the local analyzer patterns before I write the checker, so the implementation matches what this tree can actually compile.I’ve got the rule shape; next I’m locating any existing checker code in-tree that handles branch conditions, AST bodies, or allocation tracking so the plugin stays within the APIs already present here.```cpp
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Expr.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/SourceLocation.h"
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

  class BodyVisitor : public RecursiveASTVisitor<BodyVisitor> {
  public:
    struct UseSite {
      const DeclRefExpr *Ref = nullptr;
      const Expr *ExprNode = nullptr;
      const VarDecl *Var = nullptr;
      unsigned Order = 0;
    };

    explicit BodyVisitor(ASTContext &Ctx) : Ctx(Ctx) {}

    void setDecl(const Decl *D) {
      RootDecl = D;
      if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D))
        RootBody = FD->getBody();
      else if (const auto *VD = dyn_cast_or_null<VarDecl>(D))
        if (const Expr *Init = VD->getInit())
          RootBody = Init;
    }

    const std::vector<UseSite> &getUses() const { return Uses; }

    bool VisitDeclStmt(DeclStmt *DS) {
      for (DeclStmt::decl_iterator I = DS->decl_begin(), E = DS->decl_end();
           I != E; ++I) {
        if (const auto *VD = dyn_cast<VarDecl>(*I)) {
          if (const Expr *Init = VD->getInit())
            checkExpr(Init, VD);
        }
      }
      return true;
    }

    bool VisitBinaryOperator(BinaryOperator *BO) {
      if (!BO->isAssignmentOp())
        return true;
      const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
      if (const auto *DRE = dyn_cast<DeclRefExpr>(LHS))
        checkExpr(RHS, DRE->getDecl());
      return true;
    }

    bool VisitReturnStmt(ReturnStmt *RS) {
      if (const Expr *Ret = RS->getRetValue())
        checkExpr(Ret, nullptr);
      return true;
    }

    bool VisitUnaryOperator(UnaryOperator *UO) {
      if (UO->getOpcode() == UO_Deref)
        noteUse(UO->getSubExpr()->IgnoreParenImpCasts(), UO);
      return true;
    }

    bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
      noteUse(ASE->getBase()->IgnoreParenImpCasts(), ASE);
      noteUse(ASE->getIdx()->IgnoreParenImpCasts(), ASE);
      return true;
    }

    bool VisitMemberExpr(MemberExpr *ME) {
      noteUse(ME->getBase()->IgnoreParenImpCasts(), ME);
      return true;
    }

    bool VisitCallExpr(CallExpr *CE) {
      for (const Expr *Arg : CE->arguments())
        noteUse(Arg->IgnoreParenImpCasts(), CE);
      return true;
    }

    bool VisitIfStmt(IfStmt *IS) {
      if (const Expr *Cond = IS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitWhileStmt(WhileStmt *WS) {
      if (const Expr *Cond = WS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitForStmt(ForStmt *FS) {
      if (const Expr *Cond = FS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitConditionalOperator(ConditionalOperator *CO) {
      checkCondition(CO->getCond()->IgnoreParenImpCasts());
      return true;
    }

  private:
    ASTContext &Ctx;
    const Decl *RootDecl = nullptr;
    const Stmt *RootBody = nullptr;
    std::vector<UseSite> Uses;
    unsigned NextOrder = 0;
    std::set<const VarDecl *> CheckedVars;

    static bool isMallocLikeName(StringRef Name) {
      return Name == "malloc" || Name == "calloc" || Name == "realloc";
    }

    bool isAllocationCall(const Expr *E) const {
      const auto *CE = dyn_cast_or_null<CallExpr>(E->IgnoreParenImpCasts());
      if (!CE)
        return false;
      const FunctionDecl *FD = CE->getDirectCallee();
      if (!FD)
        return false;
      return isMallocLikeName(FD->getName());
    }

    const VarDecl *getVarFromExpr(const Expr *E) const {
      E = E ? E->IgnoreParenImpCasts() : nullptr;
      if (!E)
        return nullptr;
      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());
      if (const auto *UO = dyn_cast<UnaryOperator>(E))
        return getVarFromExpr(UO->getSubExpr());
      if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
        if (const VarDecl *V = getVarFromExpr(BO->getLHS()))
          return V;
        return getVarFromExpr(BO->getRHS());
      }
      return nullptr;
    }

    void noteUse(const Expr *E, const Stmt *S) {
      const VarDecl *V = getVarFromExpr(E);
      if (!V)
        return;
      Uses.push_back({dyn_cast<DeclRefExpr>(E->IgnoreParenImpCasts()), dyn_cast<const Expr>(S), V, NextOrder++});
    }

    void checkCondition(const Expr *E) {
      const auto *DRE = dyn_cast_or_null<DeclRefExpr>(E->IgnoreParenImpCasts());
      if (!DRE)
        return;
      if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
        CheckedVars.insert(VD);
    }

    void checkExpr(const Expr *E, const VarDecl *AssignedVar) {
      if (!E)
        return;
      if (isAllocationCall(E)) {
        if (AssignedVar)
          AllocatedVars.insert(AssignedVar);
      }
      for (const Stmt *Child : E->children()) {
        if (const auto *ChildE = dyn_cast_or_null<Expr>(Child))
          checkExpr(ChildE, AssignedVar);
      }
    }

    std::set<const VarDecl *> AllocatedVars;
  };

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

  static bool isMallocLikeCall(const Expr *E) {
    const auto *CE = dyn_cast_or_null<CallExpr>(E->IgnoreParenImpCasts());
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const VarDecl *getTrackedVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static bool isNullCheckCond(const Expr *E, const VarDecl *V) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == V;
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_LNot &&
             isNullCheckCond(UO->getSubExpr(), V);
    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;
      return (isTrackedVarFromExpr(BO->getLHS()) == V &&
              BO->getRHS()->isNullPointerConstant(
                  E->getExprLoc(), Expr::NPC_ValueDependentIsNull)) ||
             (isTrackedVarFromExpr(BO->getRHS()) == V &&
              BO->getLHS()->isNullPointerConstant(
                  E->getExprLoc(), Expr::NPC_ValueDependentIsNull));
    }
    return false;
  }

  static bool isUseOfVar(const Expr *E, const VarDecl *V) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == V;
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return isUseOfVar(UO->getSubExpr(), V);
    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return isUseOfVar(BO->getLHS(), V) || isUseOfVar(BO->getRHS(), V);
    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return isUseOfVar(ME->getBase(), V);
    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return isUseOfVar(ASE->getBase(), V) || isUseOfVar(ASE->getIdx(), V);
    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isUseOfVar(Arg, V))
          return true;
    }
    return false;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    std::vector<const Stmt *> Stmts;
    llvm::SmallVector<const Stmt *, 32> Worklist;
    Worklist.push_back(Body);
    while (!Worklist.empty()) {
      const Stmt *S = Worklist.pop_back_val();
      Stmts.push_back(S);
      for (const Stmt *Child : S->children())
        if (Child)
          Worklist.push_back(Child);
    }

    std::set<const VarDecl *> Allocated;
    std::set<const VarDecl *> Checked;
    std::set<const VarDecl *> Reported;

    auto markAllocFromExpr = [&](const Expr *E) {
      const auto *BO = dyn_cast_or_null<BinaryOperator>(E);
      if (!BO || !BO->isAssignmentOp())
        return;
      const VarDecl *V = getTrackedVarFromExpr(BO->getLHS());
      if (!V)
        return;
      if (isMallocLikeCall(BO->getRHS()))
        Allocated.insert(V);
    };

    for (const Stmt *S : Stmts) {
      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *DD : DS->decls()) {
          const auto *VD = dyn_cast<VarDecl>(DD);
          if (!VD)
            continue;
          if (const Expr *Init = VD->getInit())
            if (isMallocLikeCall(Init))
              Allocated.insert(VD);
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(S))
        markAllocFromExpr(cast<Expr>(S));

      if (const auto *IS = dyn_cast<IfStmt>(S)) {
        const Expr *Cond = IS->getCond();
        if (const auto *V = getTrackedVarFromExpr(Cond))
          Checked.insert(V);
      } else if (const auto *WS = dyn_cast<WhileStmt>(S)) {
        if (const auto *V = getTrackedVarFromExpr(WS->getCond()))
          Checked.insert(V);
      } else if (const auto *FS = dyn_cast<ForStmt>(S)) {
        if (const Expr *Cond = FS->getCond())
          if (const auto *V = getTrackedVarFromExpr(Cond))
            Checked.insert(V);
      } else if (const auto *DS = dyn_cast<DoStmt>(S)) {
        if (const auto *V = getTrackedVarFromExpr(DS->getCond()))
          Checked.insert(V);
      }

      for (const VarDecl *V : Allocated) {
        if (Reported.count(V))
          continue;

        bool HasCheckBeforeUse = false;
        for (const Stmt *Later : Stmts) {
          if (Later == S)
            continue;
          if (const auto *IFS = dyn_cast<IfStmt>(Later)) {
            if (isNullCheckCond(IFS->getCond(), V)) {
              HasCheckBeforeUse = true;
              continue;
            }
          }
          if (isUseOfVar(dyn_cast_or_null<Expr>(Later), V)) {
            if (!HasCheckBeforeUse) {
              emitASTReport(Later, AM.getAnalysisDeclContext(), BR);
              Reported.insert(V);
            }
            break;
          }
        }
      }
    }
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