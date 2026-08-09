I’m checking the existing analyzer hooks and then I’ll wire the checker into the AST body walk so it can track allocation, null checks, and first use in one pass.```cpp
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
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

  struct VarInfo {
    const VarDecl *VD = nullptr;
    bool AllocSeen = false;
    bool Checked = false;
    bool Used = false;
    bool Reported = false;
    unsigned AllocSeq = 0;
    const Expr *AllocExpr = nullptr;
  };

  static bool isNullConstant(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return E->isNullPointerConstant(*nullptr, Expr::NPC_ValueDependentIsNotNull);
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

  static const VarDecl *getTrackedVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static const VarDecl *getTrackedVarFromLHS(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      if (UO->getOpcode() == UO_Deref)
        return getTrackedVarFromExpr(UO->getSubExpr());
    return getTrackedVarFromExpr(E);
  }

  static bool isDirectUseOfTrackedVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_Deref && isDirectUseOfTrackedVar(UO->getSubExpr(), VD);
    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return isDirectUseOfTrackedVar(BO->getLHS(), VD) || isDirectUseOfTrackedVar(BO->getRHS(), VD);
    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isDirectUseOfTrackedVar(Arg, VD))
          return true;
    }
    return false;
  }

  static bool exprMentionsTrackedVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;
    for (const Stmt *Child : E->children()) {
      if (const auto *CE = dyn_cast_or_null<Expr>(Child))
        if (exprMentionsTrackedVar(CE, VD))
          return true;
    }
    return false;
  }

  static bool isNullCheckConditionForVar(const Expr *Cond, const VarDecl *VD) {
    if (!Cond || !VD)
      return false;
    Cond = Cond->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond))
      return UO->getOpcode() == UO_LNot && exprMentionsTrackedVar(UO->getSubExpr(), VD);

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!exprMentionsTrackedVar(BO->getLHS(), VD) &&
          !exprMentionsTrackedVar(BO->getRHS(), VD))
        return false;
      if (BO->getOpcode() == BO_EQ || BO->getOpcode() == BO_NE)
        return isNullConstant(BO->getLHS()) || isNullConstant(BO->getRHS());
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return DRE->getDecl() == VD;

    return false;
  }

  static const Expr *skipToBody(const Stmt *S) {
    if (!S)
      return nullptr;
    if (const auto *CS = dyn_cast<CompoundStmt>(S))
      return CS;
    return S;
  }

  void reportViolation(const VarInfo &Info, const Stmt *At, AnalysisDeclContext *ADC,
                       BugReporter &BR) const {
    if (!At || !ADC || !Info.VD)
      return;
    PathDiagnosticLocation Location(At->getBeginLoc(), BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(At->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void scanExpr(const Expr *E, std::vector<VarInfo> &Vars, AnalysisDeclContext *ADC,
                BugReporter &BR) const {
    if (!E)
      return;

    E = E->IgnoreParenImpCasts();

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      if (isAllocationCall(CE)) {
        const Expr *ArgExpr = nullptr;
        if (CE->getNumArgs() > 0)
          ArgExpr = CE->getArg(0);
        if (const auto *VD = getTrackedVarFromLHS(ArgExpr)) {
          for (auto &V : Vars) {
            if (V.VD == VD) {
              V.AllocSeen = true;
              V.Checked = false;
              V.Used = false;
              V.Reported = false;
              V.AllocSeq++;
              V.AllocExpr = E;
              return;
            }
          }
        }
      }
      for (const Expr *Arg : CE->arguments())
        scanExpr(Arg, Vars, ADC, BR);
      return;
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      const Expr *Sub = UO->getSubExpr();
      if (UO->getOpcode() == UO_Deref) {
        if (const VarDecl *VD = getTrackedVarFromExpr(Sub)) {
          for (auto &V : Vars) {
            if (V.VD == VD && V.AllocSeen && !V.Checked && !V.Reported) {
              V.Used = true;
              V.Reported = true;
              reportViolation(V, E, ADC, BR);
              return;
            }
          }
        }
      }
      scanExpr(Sub, Vars, ADC, BR);
      return;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (isNullCheckConditionForVar(BO->getLHS(), getTrackedVarFromExpr(BO->getRHS())))
        ;
      scanExpr(BO->getLHS(), Vars, ADC, BR);
      scanExpr(BO->getRHS(), Vars, ADC, BR);
      return;
    }

    for (const Stmt *Child : E->children()) {
      if (const auto *CE = dyn_cast_or_null<Expr>(Child))
        scanExpr(CE, Vars, ADC, BR);
    }
  }

  void scanStmt(const Stmt *S, std::vector<VarInfo> &Vars, AnalysisDeclContext *ADC,
                BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body())
        scanStmt(Child, Vars, ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const DeclStmt::const_decl_iterator I = DS->decl_begin(); I != DS->decl_end(); ++I) {
        if (const auto *VD = dyn_cast<VarDecl>(*I)) {
          VarInfo VI;
          VI.VD = VD;
          Vars.push_back(VI);
          if (const Expr *Init = VD->getInit()) {
            scanExpr(Init, Vars, ADC, BR);
            if (const auto *CE = dyn_cast<CallExpr>(Init->IgnoreParenImpCasts()))
              if (isAllocationCall(CE))
                Vars.back().AllocSeen = true;
          }
        }
      }
      return;
    }

    if (const auto *IF = dyn_cast<IfStmt>(S)) {
      const Expr *Cond = IF->getCond();
      for (auto &V : Vars)
        if (V.AllocSeen && !V.Checked && isNullCheckConditionForVar(Cond, V.VD))
          V.Checked = true;

      scanExpr(Cond, Vars, ADC, BR);
      scanStmt(IF->getThen(), Vars, ADC, BR);
      scanStmt(IF->getElse(), Vars, ADC, BR);
      return;
    }

    if (const auto *WH = dyn_cast<WhileStmt>(S)) {
      const Expr *Cond = WH->getCond();
      for (auto &V : Vars)
        if (V.AllocSeen && !V.Checked && isNullCheckConditionForVar(Cond, V.VD))
          V.Checked = true;
      scanExpr(Cond, Vars, ADC, BR);
      scanStmt(WH->getBody(), Vars, ADC, BR);
      return;
    }

    if (const auto *DO = dyn_cast<DoStmt>(S)) {
      scanStmt(DO->getBody(), Vars, ADC, BR);
      scanExpr(DO->getCond(), Vars, ADC, BR);
      return;
    }

    if (const auto *FOR = dyn_cast<ForStmt>(S)) {
      scanStmt(FOR->getInit(), Vars, ADC, BR);
      scanExpr(FOR->getCond(), Vars, ADC, BR);
      scanExpr(FOR->getInc(), Vars, ADC, BR);
      scanStmt(FOR->getBody(), Vars, ADC, BR);
      return;
    }

    if (const auto *RS = dyn_cast<ReturnStmt>(S)) {
      scanExpr(RS->getRetValue(), Vars, ADC, BR);
      return;
    }

    if (const auto *ES = dyn_cast<Expr>(S)) {
      scanExpr(ES, Vars, ADC, BR);
      return;
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, Vars, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    std::vector<VarInfo> Vars;
    scanStmt(Body, Vars, ADC, BR);
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