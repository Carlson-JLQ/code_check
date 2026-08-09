I’m checking the existing plugin template and the analyzer APIs you already have in hand, then I’ll wire the checker logic directly into that single C++ file. The main constraint is to stay within the shown checker interfaces and emit exactly one warning per offending allocation variable.```cpp
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

  static bool isNullPtrLiteral(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E);
  }

  static const Expr *stripParenImpCasts(const Expr *E) {
    return E ? E->IgnoreParenImpCasts() : nullptr;
  }

  static const DeclRefExpr *getDeclRefExpr(const Expr *E) {
    if (!E)
      return nullptr;
    return dyn_cast<DeclRefExpr>(stripParenImpCasts(E));
  }

  static const VarDecl *getCandidateVarFromAllocCall(const CallExpr *CE) {
    if (!CE)
      return nullptr;

    const Expr *Callee = CE->getCallee()->IgnoreParenImpCasts();
    const FunctionDecl *FD = dyn_cast_or_null<FunctionDecl>(CE->getDirectCallee());
    if (!FD)
      return nullptr;

    StringRef Name = FD->getName();
    if (Name != "malloc" && Name != "calloc" && Name != "realloc")
      return nullptr;

    const Expr *Parent = CE->getStoredCallee();
    (void)Parent;

    const auto *Outer = dyn_cast_or_null<BinaryOperator>(nullptr);
    (void)Outer;

    return nullptr;
  }

  static bool isAllocationFunction(const CallExpr *CE) {
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const VarDecl *getAssignedVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;

    E = E->IgnoreParenImpCasts();

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isAssignmentOp())
        return nullptr;
      const auto *DRE = getDeclRefExpr(BO->getLHS());
      return DRE ? dyn_cast<VarDecl>(DRE->getDecl()) : nullptr;
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      (void)UO;
    }

    return nullptr;
  }

  static const VarDecl *getAssignedVarFromStmt(const Stmt *S) {
    const auto *E = dyn_cast_or_null<Expr>(S);
    return E ? getAssignedVarFromExpr(E) : nullptr;
  }

  static bool exprMentionsVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;

    E = E->IgnoreParenImpCasts();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;

    for (const Stmt *Child : E->children()) {
      const auto *ChildExpr = dyn_cast_or_null<Expr>(Child);
      if (exprMentionsVar(ChildExpr, VD))
        return true;
    }
    return false;
  }

  static bool isNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
    if (!Cond || !VD)
      return false;

    Cond = Cond->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return exprMentionsVar(UO->getSubExpr(), VD);
      return false;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!(BO->isEqualityOp() || BO->isRelationalOp()))
        return false;
      const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
      const auto *LHSRef = dyn_cast<DeclRefExpr>(LHS);
      const auto *RHSRef = dyn_cast<DeclRefExpr>(RHS);
      if (LHSRef && LHSRef->getDecl() == VD && isNullPtrLiteral(RHS))
        return true;
      if (RHSRef && RHSRef->getDecl() == VD && isNullPtrLiteral(LHS))
        return true;
      return false;
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return DRE->getDecl() == VD;

    return false;
  }

  void emitReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  static const Expr *getInitializerExpr(const DeclStmt *DS, const VarDecl *VD) {
    if (!DS || !VD)
      return nullptr;
    for (const auto *D : DS->decls()) {
      const auto *CurVD = dyn_cast<VarDecl>(D);
      if (CurVD == VD)
        return CurVD->getInit();
    }
    return nullptr;
  }

  static const Expr *getTopExpr(const Stmt *S) {
    return dyn_cast_or_null<Expr>(S);
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

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    SmallPtrSet<const VarDecl *, 16> Reported;
    SmallVector<const VarDecl *, 16> LiveAllocVars;
    SmallVector<const VarDecl *, 16> PendingReallocVars;

    auto markAllocation = [&](const VarDecl *VD, const Expr *AllocSite) {
      if (!VD)
        return;
      if (Reported.contains(VD))
        return;
      if (llvm::is_contained(LiveAllocVars, VD))
        return;
      if (const auto *InitCE = dyn_cast_or_null<CallExpr>(AllocSite)) {
        if (isAllocationFunction(InitCE))
          LiveAllocVars.push_back(VD);
      }
    };

    std::function<void(const Stmt *, bool)> Visit = [&](const Stmt *S,
                                                        bool Guarded) {
      if (!S)
        return;

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const auto *D : DS->decls()) {
          const auto *VD = dyn_cast<VarDecl>(D);
          if (!VD)
            continue;
          const Expr *Init = VD->getInit();
          const auto *CE = dyn_cast_or_null<CallExpr>(Init ? Init->IgnoreParenImpCasts() : nullptr);
          if (CE && isAllocationFunction(CE))
            markAllocation(VD, CE);
        }
      }

      if (const auto *IfS = dyn_cast<IfStmt>(S)) {
        const Expr *Cond = IfS->getCond();
        bool CondChecksVar = false;
        for (const VarDecl *VD : LiveAllocVars) {
          if (isNullCheckCondition(Cond, VD))
            CondChecksVar = true;
        }
        Visit(IfS->getCond(), Guarded);
        Visit(IfS->getThen(), Guarded || CondChecksVar);
        Visit(IfS->getElse(), Guarded);
        return;
      }

      if (const auto *ForS = dyn_cast<ForStmt>(S)) {
        Visit(ForS->getInit(), Guarded);
        Visit(ForS->getCond(), Guarded);
        Visit(ForS->getInc(), Guarded);
        Visit(ForS->getBody(), Guarded);
        return;
      }

      if (const auto *WhileS = dyn_cast<WhileStmt>(S)) {
        Visit(WhileS->getCond(), Guarded);
        Visit(WhileS->getBody(), Guarded);
        return;
      }

      if (const auto *DoS = dyn_cast<DoStmt>(S)) {
        Visit(DoS->getBody(), Guarded);
        Visit(DoS->getCond(), Guarded);
        return;
      }

      if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
        for (const Stmt *Child : CS->body()) {
          if (const auto *InnerDS = dyn_cast<DeclStmt>(Child)) {
            for (const auto *D : InnerDS->decls()) {
              const auto *VD = dyn_cast<VarDecl>(D);
              if (!VD)
                continue;
              const Expr *Init = VD->getInit();
              const auto *CE =
                  dyn_cast_or_null<CallExpr>(Init ? Init->IgnoreParenImpCasts() : nullptr);
              if (CE && isAllocationFunction(CE))
                markAllocation(VD, CE);
            }
          }

          for (const VarDecl *VD : LiveAllocVars) {
            if (Reported.contains(VD))
              continue;

            if (const auto *E = getTopExpr(Child)) {
              if (const auto *Assign = dyn_cast<BinaryOperator>(E->IgnoreParenImpCasts())) {
                if (Assign->isAssignmentOp()) {
                  const auto *LHS = getDeclRefExpr(Assign->getLHS());
                  if (LHS && LHS->getDecl() == VD) {
                    const Expr *RHS = Assign->getRHS()->IgnoreParenImpCasts();
                    if (const auto *CE = dyn_cast<CallExpr>(RHS)) {
                      if (isAllocationFunction(CE)) {
                        PendingReallocVars.push_back(VD);
                        continue;
                      }
                    }
                  }
                }
              }

              if (exprMentionsVar(E, VD)) {
                if (!Guarded) {
                  emitReport(E, ADC, BR);
                  Reported.insert(VD);
                }
              }
            }
          }

          Visit(Child, Guarded);
        }
        return;
      }

      for (const Stmt *Child : S->children())
        Visit(Child, Guarded);
    };

    Visit(Body, false);
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