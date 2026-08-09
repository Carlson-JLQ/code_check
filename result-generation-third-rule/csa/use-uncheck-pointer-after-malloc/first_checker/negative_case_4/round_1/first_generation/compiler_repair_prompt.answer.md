I’m reducing this to the compile breaks first, then I’ll keep the checker shape and names intact while stripping the broken internal helper path.```cpp
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
class GeneratedUseUncheckPointerAfterMallocChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static bool isMallocLikeCall(const Expr *E) {
    if (!E)
      return false;

    E = E->IgnoreParenImpCasts();
    const auto *CE = dyn_cast<CallExpr>(E);
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

    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return getTrackedVarFromExpr(UO->getSubExpr());

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (const VarDecl *V = getTrackedVarFromExpr(BO->getLHS()))
        return V;
      return getTrackedVarFromExpr(BO->getRHS());
    }

    return nullptr;
  }

  static bool isNullCheckCond(const Expr *E, const VarDecl *V, ASTContext &Ctx) {
    if (!E || !V)
      return false;

    E = E->IgnoreParenImpCasts();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == V;

    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_LNot && isNullCheckCond(UO->getSubExpr(), V, Ctx);

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;

      return (getTrackedVarFromExpr(BO->getLHS()) == V &&
              BO->getRHS()->isNullPointerConstant(Ctx, Expr::NPC_ValueDependentIsNull)) ||
             (getTrackedVarFromExpr(BO->getRHS()) == V &&
              BO->getLHS()->isNullPointerConstant(Ctx, Expr::NPC_ValueDependentIsNull));
    }

    return false;
  }

  static bool isUseOfVar(const Expr *E, const VarDecl *V) {
    if (!E || !V)
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

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    ASTContext &Ctx = AM.getASTContext();
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    llvm::SmallVector<const Stmt *, 32> Worklist;
    llvm::SmallVector<const Stmt *, 32> Stmts;
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

      if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
        if (BO->isAssignmentOp()) {
          const VarDecl *V = getTrackedVarFromExpr(BO->getLHS());
          if (V && isMallocLikeCall(BO->getRHS()))
            Allocated.insert(V);
        }
      }

      if (const auto *IS = dyn_cast<IfStmt>(S)) {
        if (const VarDecl *V = getTrackedVarFromExpr(IS->getCond()))
          Checked.insert(V);
      } else if (const auto *WS = dyn_cast<WhileStmt>(S)) {
        if (const VarDecl *V = getTrackedVarFromExpr(WS->getCond()))
          Checked.insert(V);
      } else if (const auto *FS = dyn_cast<ForStmt>(S)) {
        if (const VarDecl *V = getTrackedVarFromExpr(FS->getCond()))
          Checked.insert(V);
      } else if (const auto *DS = dyn_cast<DoStmt>(S)) {
        if (const VarDecl *V = getTrackedVarFromExpr(DS->getCond()))
          Checked.insert(V);
      }

      for (const VarDecl *V : Allocated) {
        if (Reported.count(V))
          continue;

        bool SeenCheck = Checked.count(V) != 0;
        for (const Stmt *Later : Stmts) {
          if (Later == S)
            continue;

          if (const auto *IFS = dyn_cast<IfStmt>(Later)) {
            if (isNullCheckCond(IFS->getCond(), V, Ctx)) {
              SeenCheck = true;
              continue;
            }
          } else if (const auto *WS = dyn_cast<WhileStmt>(Later)) {
            if (isNullCheckCond(WS->getCond(), V, Ctx)) {
              SeenCheck = true;
              continue;
            }
          } else if (const auto *FS = dyn_cast<ForStmt>(Later)) {
            if (isNullCheckCond(FS->getCond(), V, Ctx)) {
              SeenCheck = true;
              continue;
            }
          } else if (const auto *DS2 = dyn_cast<DoStmt>(Later)) {
            if (isNullCheckCond(DS2->getCond(), V, Ctx)) {
              SeenCheck = true;
              continue;
            }
          }

          if (const auto *LaterExpr = dyn_cast<Expr>(Later)) {
            if (isUseOfVar(LaterExpr, V) && !SeenCheck) {
              emitASTReport(Later, ADC, BR);
              Reported.insert(V);
              break;
            }
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