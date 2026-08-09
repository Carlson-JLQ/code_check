I’ve got the shape of the fix: remove the non-existent AST APIs, replace the placeholder casts with actual AST traversal, and keep the checker registration and report surface unchanged. I’m editing the single implementation file now and will verify the compile-sensitive pieces against the existing Clang API usage.```cpp
#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ParentMapContext.h"
#include "clang/Basic/SourceManager.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"
#include "llvm/ADT/SmallPtrSet.h"

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

  static const DeclRefExpr *getDeclRefExpr(const Expr *E) {
    if (!E)
      return nullptr;
    return dyn_cast<DeclRefExpr>(E->IgnoreParenImpCasts());
  }

  static const VarDecl *getAssignedVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;

    E = E->IgnoreParenImpCasts();

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isAssignmentOp())
        return nullptr;
      if (const auto *DRE = getDeclRefExpr(BO->getLHS()))
        return dyn_cast<VarDecl>(DRE->getDecl());
    }

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

  static const VarDecl *getAllocatedVar(const Stmt *S) {
    const auto *DS = dyn_cast_or_null<DeclStmt>(S);
    if (!DS)
      return nullptr;

    for (const Decl *D : DS->decls()) {
      const auto *VD = dyn_cast<VarDecl>(D);
      if (!VD)
        continue;
      const Expr *Init = VD->getInit();
      const auto *CE =
          dyn_cast_or_null<CallExpr>(Init ? Init->IgnoreParenImpCasts() : nullptr);
      if (isAllocationFunction(CE))
        return VD;
    }
    return nullptr;
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

      if (const auto *LHSRef = dyn_cast<DeclRefExpr>(LHS))
        if (LHSRef->getDecl() == VD && isNullPtrLiteral(RHS))
          return true;

      if (const auto *RHSRef = dyn_cast<DeclRefExpr>(RHS))
        if (RHSRef->getDecl() == VD && isNullPtrLiteral(LHS))
          return true;
      return false;
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return DRE->getDecl() == VD;

    return false;
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

  static bool usesVarInStmt(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return false;

    if (const auto *E = dyn_cast<Expr>(S))
      return exprMentionsVar(E, VD);

    for (const Stmt *Child : S->children()) {
      if (usesVarInStmt(Child, VD))
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

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    llvm::SmallPtrSet<const VarDecl *, 16> Reported;
    llvm::SmallPtrSet<const VarDecl *, 16> Allocated;

    std::function<void(const Stmt *, bool)> Visit = [&](const Stmt *S,
                                                        bool Guarded) {
      if (!S)
        return;

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        if (const VarDecl *VD = getAllocatedVar(DS))
          Allocated.insert(VD);
      }

      if (const auto *IfS = dyn_cast<IfStmt>(S)) {
        bool BranchGuardsVar = false;
        for (const VarDecl *VD : Allocated) {
          if (isNullCheckCondition(IfS->getCond(), VD)) {
            BranchGuardsVar = true;
            break;
          }
        }
        Visit(IfS->getCond(), Guarded);
        Visit(IfS->getThen(), Guarded || BranchGuardsVar);
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
          if (const auto *E = dyn_cast<Expr>(Child)) {
            for (const VarDecl *VD : Allocated) {
              if (Reported.contains(VD))
                continue;
              if (usesVarInStmt(E, VD) && !Guarded) {
                emitASTReport(E, ADC, BR);
                Reported.insert(VD);
              }
            }
          }

          if (const auto *VD = getAllocatedVar(Child))
            Allocated.insert(VD);

          for (const VarDecl *Tracked : Allocated) {
            if (Reported.contains(Tracked))
              continue;
            if (const auto *E = dyn_cast<Expr>(Child)) {
              if (const auto *AssignVar = getAssignedVarFromExpr(E)) {
                if (AssignVar == Tracked) {
                  const auto *BO = dyn_cast<BinaryOperator>(E->IgnoreParenImpCasts());
                  if (BO && BO->isAssignmentOp()) {
                    const auto *RHS =
                        dyn_cast_or_null<CallExpr>(BO->getRHS()->IgnoreParenImpCasts());
                    if (isAllocationFunction(RHS))
                      continue;
                  }
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