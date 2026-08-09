#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ExprCXX.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Type.h"
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

  struct VarState {
    const VarDecl *VD = nullptr;
    bool Allocated = false;
    bool CheckedSinceAlloc = false;
    bool UsedSinceAlloc = false;
    SourceLocation AllocLoc;
    SourceLocation FirstUseLoc;
    bool Reported = false;
  };

  static const VarDecl *getBaseVar(const Expr *E) {
    if (!E)
      return nullptr;

    const Expr *Cur = E->IgnoreParenImpCasts();
    while (true) {
      if (const auto *DRE = dyn_cast<DeclRefExpr>(Cur))
        return dyn_cast<VarDecl>(DRE->getDecl());

      if (const auto *ME = dyn_cast<MemberExpr>(Cur)) {
        Cur = ME->getBase()->IgnoreParenImpCasts();
        continue;
      }

      if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(Cur)) {
        Cur = ASE->getBase()->IgnoreParenImpCasts();
        continue;
      }

      if (const auto *UO = dyn_cast<UnaryOperator>(Cur)) {
        if (UO->getOpcode() == UO_Deref || UO->getOpcode() == UO_AddrOf) {
          Cur = UO->getSubExpr()->IgnoreParenImpCasts();
          continue;
        }
      }

      if (const auto *CE = dyn_cast<CastExpr>(Cur)) {
        Cur = CE->getSubExpr()->IgnoreParenImpCasts();
        continue;
      }

      break;
    }
    return nullptr;
  }

  static bool isNullConstant(const Expr *E, ASTContext &Ctx) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return E->isNullPointerConstant(Ctx,
                                    Expr::NPC_ValueDependentIsNotNull);
  }

  static bool isAllocationCall(const Expr *E) {
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

  static const Expr *getAssignmentRHS(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || BO->getOpcode() != BO_Assign)
      return nullptr;
    return BO->getRHS();
  }

  static bool isNullCheckExpr(const Expr *E, const VarDecl *VD,
                              ASTContext &Ctx) {
    if (!E || !VD)
      return false;

    E = E->IgnoreParenImpCasts();

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;

      const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
      const VarDecl *LV = getBaseVar(L);
      const VarDecl *RV = getBaseVar(R);

      return (LV == VD && isNullConstant(R, Ctx)) ||
             (RV == VD && isNullConstant(L, Ctx));
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() != UO_LNot)
        return false;
      const Expr *Sub = UO->getSubExpr()->IgnoreParenImpCasts();
      return getBaseVar(Sub) == VD;
    }

    return getBaseVar(E) == VD;
  }

  static bool isSimpleUseOfVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;

    E = E->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_Deref || UO->getOpcode() == UO_AddrOf)
        return getBaseVar(UO->getSubExpr()) == VD;
      return false;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return getBaseVar(BO->getLHS()) == VD || getBaseVar(BO->getRHS()) == VD;

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (getBaseVar(Arg) == VD)
          return true;
      return false;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return getBaseVar(ME->getBase()) == VD;

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return getBaseVar(ASE->getBase()) == VD || getBaseVar(ASE->getIdx()) == VD;

    return getBaseVar(E) == VD;
  }

  static void collectStmts(const Stmt *S, std::vector<const Stmt *> &Out) {
    if (!S)
      return;
    Out.push_back(S);
    for (const Stmt *Child : S->children())
      collectStmts(Child, Out);
  }

  void report(const VarDecl *VD, SourceLocation Loc, AnalysisDeclContext *ADC,
              BugReporter &BR) const {
    if (!VD || Loc.isInvalid())
      return;
    PathDiagnosticLocation PLoc(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", PLoc);
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  static bool isPointerLikeVar(const VarDecl *VD) {
    if (!VD)
      return false;
    return VD->getType()->isAnyPointerType();
  }

  void analyzeStmt(const Stmt *S,
                   std::unordered_map<const VarDecl *, VarState> &States,
                   AnalysisDeclContext *ADC, BugReporter &BR,
                   ASTContext &Ctx) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !isPointerLikeVar(VD))
          continue;
        if (const Expr *Init = VD->getInit()) {
          if (isAllocationCall(Init)) {
            auto &St = States[VD];
            St.VD = VD;
            St.Allocated = true;
            St.CheckedSinceAlloc = false;
            St.UsedSinceAlloc = false;
            St.AllocLoc = Init->getBeginLoc();
          }
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *LVD = getBaseVar(BO->getLHS());
        if (LVD && isPointerLikeVar(LVD) && isAllocationCall(BO->getRHS())) {
          auto &St = States[LVD];
          St.VD = LVD;
          St.Allocated = true;
          St.CheckedSinceAlloc = false;
          St.UsedSinceAlloc = false;
          St.AllocLoc = BO->getRHS()->getBeginLoc();
          return;
        }
      }
    }

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      if (const Expr *Cond = If->getCond()) {
        for (auto &It : States) {
          if (It.second.Allocated && !It.second.UsedSinceAlloc &&
              isNullCheckExpr(Cond, It.first, Ctx))
            It.second.CheckedSinceAlloc = true;
        }
      }
    }

    for (auto &It : States) {
      VarState &St = It.second;
      if (!St.Allocated || St.Reported)
        continue;

      if (isSimpleUseOfVar(dyn_cast<Expr>(S), It.first) ||
          any_of(S->children(), [&](const Stmt *Child) {
            return Child && isSimpleUseOfVar(dyn_cast<Expr>(Child), It.first);
          })) {
        if (!St.CheckedSinceAlloc && !St.UsedSinceAlloc) {
          St.UsedSinceAlloc = true;
          St.FirstUseLoc = S->getBeginLoc();
          St.Reported = true;
          report(It.first, S->getBeginLoc(), ADC, BR);
        } else {
          St.UsedSinceAlloc = true;
        }
      }
    }
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    const Stmt *Body = FD->getBody();
    std::vector<const Stmt *> Stmts;
    collectStmts(Body, Stmts);

    std::unordered_map<const VarDecl *, VarState> States;
    ASTContext &Ctx = AM.getASTContext();
    for (const Stmt *S : Stmts)
      analyzeStmt(S, States, ADC, BR, Ctx);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;