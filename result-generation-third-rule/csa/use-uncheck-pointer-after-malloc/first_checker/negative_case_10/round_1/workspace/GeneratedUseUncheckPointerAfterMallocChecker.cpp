#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "clang/AST/Decl.h"
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
    const VarDecl *VD = nullptr;
    bool Checked = false;
    bool Used = false;
    bool Reported = false;
    SourceLocation FirstViolationLoc;
  };

  static bool isNullLiteralExpr(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E);
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

  static const VarDecl *getTrackedVar(const Expr *E) {
    if (!E)
      return nullptr;

    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_Deref)
        return getTrackedVar(UO->getSubExpr());
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (BO->isAssignmentOp())
        return getTrackedVar(BO->getLHS());
    }

    return nullptr;
  }

  static bool isPointerType(const VarDecl *VD) {
    return VD && VD->getType()->isPointerType();
  }

  static void collectPotentialNullChecks(const Expr *Cond,
                                         std::unordered_set<const VarDecl *> &Out) {
    if (!Cond)
      return;

    Cond = Cond->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot) {
        if (const VarDecl *VD = getTrackedVar(UO->getSubExpr()))
          Out.insert(VD);
        return;
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (BO->isComparisonOp()) {
        const VarDecl *L = getTrackedVar(BO->getLHS());
        const VarDecl *R = getTrackedVar(BO->getRHS());
        if (L && isNullLiteralExpr(BO->getRHS()))
          Out.insert(L);
        if (R && isNullLiteralExpr(BO->getLHS()))
          Out.insert(R);
      }
    } else if (const VarDecl *VD = getTrackedVar(Cond)) {
      Out.insert(VD);
    }
  }

  static void collectUses(const Stmt *S, std::vector<const VarDecl *> &Out) {
    if (!S)
      return;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(S)) {
      if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
        Out.push_back(VD);
      return;
    }

    for (const Stmt *Child : S->children())
      collectUses(Child, Out);
  }

  static void collectAssignmentLHSVars(const Stmt *S,
                                       std::vector<const VarDecl *> &Out) {
    if (!S)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        if (const VarDecl *VD = getTrackedVar(BO->getLHS()))
          Out.push_back(VD);
      }
    }

    for (const Stmt *Child : S->children())
      collectAssignmentLHSVars(Child, Out);
  }

  void emitReport(const Stmt *Violation, const VarDecl *VD, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    if (!Violation || !VD)
      return;

    PathDiagnosticLocation Location(Violation->getBeginLoc(), BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    if (ADC)
      Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void markUse(const Stmt *UseStmt, VarState &State, AnalysisDeclContext *ADC,
               BugReporter &BR) const {
    if (State.Reported || !State.Checked || State.Used)
      return;

    State.Used = true;
    State.Reported = true;
    State.FirstViolationLoc = UseStmt->getBeginLoc();
    emitReport(UseStmt, State.VD, ADC, BR);
  }

  void processStmt(const Stmt *S,
                   std::unordered_map<const VarDecl *, VarState> &States,
                   AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !isPointerType(VD) || !VD->hasInit())
          continue;
        const Expr *Init = VD->getInit()->IgnoreParenImpCasts();
        const auto *CE = dyn_cast<CallExpr>(Init);
        if (!isAllocationCall(CE))
          continue;

        auto &State = States[VD];
        State.VD = VD;
        State.Checked = false;
        State.Used = false;
        State.Reported = false;
      }
    }

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      std::unordered_set<const VarDecl *> CheckedVars;
      collectPotentialNullChecks(IfS->getCond(), CheckedVars);
      for (const VarDecl *VD : CheckedVars) {
        auto It = States.find(VD);
        if (It != States.end())
          It->second.Checked = true;
      }

      if (const Stmt *Then = IfS->getThen())
        processStmt(Then, States, ADC, BR);
      if (const Stmt *Else = IfS->getElse())
        processStmt(Else, States, ADC, BR);
      return;
    }

    if (const auto *WhileS = dyn_cast<WhileStmt>(S)) {
      std::unordered_set<const VarDecl *> CheckedVars;
      collectPotentialNullChecks(WhileS->getCond(), CheckedVars);
      for (const VarDecl *VD : CheckedVars) {
        auto It = States.find(VD);
        if (It != States.end())
          It->second.Checked = true;
      }
      if (const Stmt *Body = WhileS->getBody())
        processStmt(Body, States, ADC, BR);
      return;
    }

    if (const auto *ForS = dyn_cast<ForStmt>(S)) {
      if (const Expr *Cond = ForS->getCond()) {
        std::unordered_set<const VarDecl *> CheckedVars;
        collectPotentialNullChecks(Cond, CheckedVars);
        for (const VarDecl *VD : CheckedVars) {
          auto It = States.find(VD);
          if (It != States.end())
            It->second.Checked = true;
        }
      }
      if (const Stmt *Body = ForS->getBody())
        processStmt(Body, States, ADC, BR);
      return;
    }

    if (const auto *DoS = dyn_cast<DoStmt>(S)) {
      if (const Stmt *Body = DoS->getBody())
        processStmt(Body, States, ADC, BR);
      if (const Expr *Cond = DoS->getCond()) {
        std::unordered_set<const VarDecl *> CheckedVars;
        collectPotentialNullChecks(Cond, CheckedVars);
        for (const VarDecl *VD : CheckedVars) {
          auto It = States.find(VD);
          if (It != States.end())
            It->second.Checked = true;
        }
      }
      return;
    }

    std::vector<const VarDecl *> AssignmentTargets;
    collectAssignmentLHSVars(S, AssignmentTargets);
    for (const VarDecl *VD : AssignmentTargets) {
      auto It = States.find(VD);
      if (It == States.end())
        continue;

      const Expr *AssignedExpr = nullptr;
      if (const auto *BO = dyn_cast<BinaryOperator>(S))
        AssignedExpr = BO->getRHS();

      if (const auto *CE = AssignedExpr ? dyn_cast<CallExpr>(AssignedExpr->IgnoreParenImpCasts()) : nullptr) {
        if (isAllocationCall(CE)) {
          It->second.Checked = false;
          It->second.Used = false;
          It->second.Reported = false;
          continue;
        }
      }

      if (const auto *CallE = dyn_cast<CallExpr>(S)) {
        bool UsesVar = false;
        for (const Expr *Arg : CallE->arguments()) {
          if (getTrackedVar(Arg) == VD) {
            UsesVar = true;
            break;
          }
        }
        if (UsesVar)
          markUse(S, It->second, ADC, BR);
      }
    }

    std::vector<const VarDecl *> Uses;
    collectUses(S, Uses);
    for (const VarDecl *VD : Uses) {
      auto It = States.find(VD);
      if (It == States.end())
        continue;

      const auto *ParentBO = dyn_cast<BinaryOperator>(S);
      if (ParentBO && ParentBO->isAssignmentOp() &&
          getTrackedVar(ParentBO->getLHS()) == VD)
        continue;

      const auto *ParentCE = dyn_cast<CallExpr>(S);
      if (ParentCE) {
        bool IsArgUse = false;
        for (const Expr *Arg : ParentCE->arguments()) {
          if (getTrackedVar(Arg) == VD) {
            IsArgUse = true;
            break;
          }
        }
        if (IsArgUse) {
          markUse(S, It->second, ADC, BR);
          continue;
        }
      }

      if (const auto *UO = dyn_cast<UnaryOperator>(S)) {
        if (UO->getOpcode() == UO_Deref && getTrackedVar(UO->getSubExpr()) == VD) {
          markUse(S, It->second, ADC, BR);
          continue;
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
        if (BO->isAssignmentOp()) {
          if (getTrackedVar(BO->getRHS()) == VD) {
            markUse(S, It->second, ADC, BR);
            continue;
          }
        }
      }

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *D : DS->decls()) {
          (void)D;
        }
      }
    }

    for (const Stmt *Child : S->children())
      processStmt(Child, States, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(FD);
    if (!ADC)
      return;

    std::unordered_map<const VarDecl *, VarState> States;
    processStmt(FD->getBody(), States, ADC, BR);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;