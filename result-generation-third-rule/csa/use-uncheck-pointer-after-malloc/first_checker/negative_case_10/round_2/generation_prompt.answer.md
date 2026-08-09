I’m checking the analyzer-facing shape of the repo and then I’ll replace the stub with a path-insensitive AST checker that tracks allocation, null checks, and first use per pointer variable.I have enough of the API surface from the retrieved context to stay within the plugin file only. Next I’m wiring the variable tracking conservatively so one warning is emitted per violating allocation target and reallocation resets the requirement.```cpp
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ParentMapContext.h"
#include "clang/Analysis/CFG.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {
struct PtrState {
  bool Allocated = false;
  bool Checked = false;
  bool Violated = false;
};

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static const Expr *strip(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    return E;
  }

  static const VarDecl *getTrackedVar(const Expr *E) {
    E = strip(E);
    if (!E)
      return nullptr;
    const auto *DRE = dyn_cast<DeclRefExpr>(E);
    if (!DRE)
      return nullptr;
    return dyn_cast<VarDecl>(DRE->getDecl());
  }

  static bool isNullLiteral(const Expr *E) {
    E = strip(E);
    if (!E)
      return false;
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E) ||
           (isa<IntegerLiteral>(E) &&
            cast<IntegerLiteral>(E)->getValue().isZero());
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

  static const Expr *getAssignedExpr(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return BO->getRHS();
  }

  static const VarDecl *getAssignedVar(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return getTrackedVar(BO->getLHS());
  }

  static bool containsUseOfVar(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return false;
    for (const Stmt *Child : S->children()) {
      if (!Child)
        continue;
      if (containsUseOfVar(Child, VD))
        return true;
    }
    const auto *DRE = dyn_cast<DeclRefExpr>(S);
    return DRE && DRE->getDecl() == VD;
  }

  static bool isNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
    Cond = strip(Cond);
    if (!Cond || !VD)
      return false;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return DRE->getDecl() == VD;

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return isNullCheckCondition(UO->getSubExpr(), VD);
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isComparisonOp())
        return false;
      const Expr *L = strip(BO->getLHS());
      const Expr *R = strip(BO->getRHS());
      return (getTrackedVar(L) == VD && isNullLiteral(R)) ||
             (getTrackedVar(R) == VD && isNullLiteral(L));
    }

    return false;
  }

  static const Stmt *getInnermostUseStmt(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD || !containsUseOfVar(S, VD))
      return nullptr;
    for (const Stmt *Child : S->children()) {
      if (const Stmt *Inner = getInnermostUseStmt(Child, VD))
        return Inner;
    }
    return S;
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

  void processStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                   llvm::DenseMap<const VarDecl *, PtrState> &States,
                   llvm::DenseSet<const VarDecl *> &Reported) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !VD->hasInit())
          continue;
        const Expr *Init = strip(VD->getInit());
        const auto *CE = dyn_cast_or_null<CallExpr>(Init);
        if (!isAllocationCall(CE))
          continue;
        PtrState &State = States[VD];
        State.Allocated = true;
        State.Checked = false;
        State.Violated = false;
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getAssignedVar(S);
        const Expr *RHS = getAssignedExpr(S);
        const auto *CE = dyn_cast_or_null<CallExpr>(strip(RHS));
        if (VD && isAllocationCall(CE)) {
          PtrState &State = States[VD];
          State.Allocated = true;
          State.Checked = false;
          State.Violated = false;
        }
      }
    }

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      if (isNullCheckCondition(If->getCond(), getTrackedVar(If->getCond()))) {
        if (const VarDecl *VD = getTrackedVar(If->getCond()))
          States[VD].Checked = true;
      } else if (const auto *Cond = strip(If->getCond())) {
        if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond)) {
          const VarDecl *VD = dyn_cast<VarDecl>(DRE->getDecl());
          if (VD)
            States[VD].Checked = true;
        }
      }
    }

    for (const Stmt *Child : S->children()) {
      processStmt(Child, ADC, BR, States, Reported);
    }

    const VarDecl *Touched = nullptr;
    if (const auto *DRE = dyn_cast<DeclRefExpr>(S))
      Touched = dyn_cast<VarDecl>(DRE->getDecl());
    if (!Touched)
      return;

    auto It = States.find(Touched);
    if (It == States.end() || !It->second.Allocated || It->second.Checked ||
        It->second.Violated || Reported.contains(Touched))
      return;

    const Stmt *UseStmt = getInnermostUseStmt(S, Touched);
    if (!UseStmt)
      return;

    It->second.Violated = true;
    Reported.insert(Touched);
    emitASTReport(UseStmt, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    const Stmt *Body = FD->getBody();
    if (!ADC || !Body)
      return;

    llvm::DenseMap<const VarDecl *, PtrState> States;
    llvm::DenseSet<const VarDecl *> Reported;
    processStmt(Body, ADC, BR, States, Reported);
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