I’m checking the local Clang Static Analyzer hooks that are already in the template and the retrieved APIs, then I’ll wire the checker to the AST so it can spot allocation, checks, and first use without touching LLVM sources.```cpp
#include <memory>
#include <utility>

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

  struct PtrState {
    bool Allocated = false;
    bool Checked = false;
    bool Used = false;
    const Expr *AllocExpr = nullptr;
    const Expr *FirstUseExpr = nullptr;
  };

  static const ImplicitCastExpr *stripParenCasts(const Expr *E) {
    while (E) {
      if (const auto *PE = dyn_cast<ParenExpr>(E)) {
        E = PE->getSubExpr();
        continue;
      }
      if (const auto *ICE = dyn_cast<ImplicitCastExpr>(E)) {
        E = ICE->getSubExpr();
        continue;
      }
      break;
    }
    return dyn_cast_or_null<ImplicitCastExpr>(E);
  }

  static const Expr *ignoreParenCasts(const Expr *E) {
    while (E) {
      if (const auto *PE = dyn_cast<ParenExpr>(E)) {
        E = PE->getSubExpr();
        continue;
      }
      if (const auto *ICE = dyn_cast<ImplicitCastExpr>(E)) {
        E = ICE->getSubExpr();
        continue;
      }
      break;
    }
    return E;
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    if (!E)
      return nullptr;
    E = ignoreParenCasts(E);
    if (const auto *DRE = dyn_cast_or_null<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static const VarDecl *getStoredVarFromLValue(const Expr *E) {
    E = ignoreParenCasts(E);
    if (!E)
      return nullptr;
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return dyn_cast<VarDecl>(ME->getMemberDecl());
    return nullptr;
  }

  static bool isNullConstant(const Expr *E) {
    if (!E)
      return false;
    E = ignoreParenCasts(E);
    if (const auto *PE = dyn_cast<ParenExpr>(E))
      E = PE->getSubExpr();
    if (isa<CXXNullPtrLiteralExpr>(E))
      return true;
    if (const auto *ICE = dyn_cast<ImplicitCastExpr>(E))
      return ICE->getCastKind() == CK_NullToPointer;
    if (const auto *ILE = dyn_cast<IntegerLiteral>(E))
      return ILE->getValue().isZero();
    return false;
  }

  static bool isAllocationCalleeName(StringRef Name) {
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const Expr *getAllocatorArgExpr(const CallExpr *CE, unsigned I) {
    if (!CE || CE->getNumArgs() <= I)
      return nullptr;
    return CE->getArg(I);
  }

  static const Stmt *findFirstUseInExpr(const Expr *E, const VarDecl *V) {
    if (!E || !V)
      return nullptr;

    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return (DRE->getDecl() == V) ? E : nullptr;

    for (const Stmt *Child : E->children()) {
      const auto *CE = dyn_cast_or_null<Expr>(Child);
      if (const Stmt *Found = findFirstUseInExpr(CE, V))
        return Found;
    }
    return nullptr;
  }

  static bool exprUsesVar(const Expr *E, const VarDecl *V) {
    return findFirstUseInExpr(E, V) != nullptr;
  }

  static bool isPointerComparisonWithNull(const Expr *Cond, const VarDecl *V) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(Cond);
    if (!BO)
      return false;
    if (!(BO->isComparisonOp() || BO->getOpcode() == BO_LAnd ||
          BO->getOpcode() == BO_LOr))
      return false;

    const Expr *L = ignoreParenCasts(BO->getLHS());
    const Expr *R = ignoreParenCasts(BO->getRHS());

    if (const auto *DRE = dyn_cast_or_null<DeclRefExpr>(L))
      if (DRE->getDecl() == V && isNullConstant(R))
        return true;

    if (const auto *DRE = dyn_cast_or_null<DeclRefExpr>(R))
      if (DRE->getDecl() == V && isNullConstant(L))
        return true;

    return false;
  }

  static bool isDirectNullCheck(const Expr *Cond, const VarDecl *V) {
    Cond = ignoreParenCasts(Cond);
    if (!Cond)
      return false;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond))
      return DRE->getDecl() == V;

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return exprUsesVar(UO->getSubExpr(), V);
    }

    return isPointerComparisonWithNull(Cond, V);
  }

  static const Stmt *findDirectUse(const Stmt *S, const VarDecl *V) {
    if (!S || !V)
      return nullptr;

    if (const auto *E = dyn_cast<Expr>(S)) {
      if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
        if (exprUsesVar(ASE->getBase(), V))
          return ASE->getBase();

      if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
        if ((UO->getOpcode() == UO_Deref || UO->isIncrementDecrementOp()) &&
            exprUsesVar(UO->getSubExpr(), V))
          return UO->getSubExpr();
      }

      if (const auto *ME = dyn_cast<MemberExpr>(E))
        if (exprUsesVar(ME->getBase(), V))
          return ME->getBase();

      if (const auto *CE = dyn_cast<CallExpr>(E)) {
        for (const Expr *Arg : CE->arguments())
          if (exprUsesVar(Arg, V))
            return Arg;
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
        if (BO->isAssignmentOp()) {
          if (exprUsesVar(BO->getRHS(), V))
            return BO->getRHS();
          return nullptr;
        }
        if (exprUsesVar(BO->getLHS(), V) || exprUsesVar(BO->getRHS(), V))
          return E;
      }
    }

    for (const Stmt *Child : S->children())
      if (const Stmt *Found = findDirectUse(Child, V))
        return Found;
    return nullptr;
  }

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    if (!Violation || !ADC)
      return;
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void handleStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                  llvm::DenseMap<const VarDecl *, PtrState> &States,
                  bool &Reported) const {
    if (!S || Reported)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *LHS = getStoredVarFromLValue(BO->getLHS());
        if (LHS && const auto *CE = dyn_cast<CallExpr>(ignoreParenCasts(BO->getRHS()))) {
          const FunctionDecl *FD = CE->getDirectCallee();
          if (FD && isAllocationCalleeName(FD->getName())) {
            PtrState &St = States[LHS];
            St.Allocated = true;
            St.Checked = false;
            St.Used = false;
            St.AllocExpr = BO;
            St.FirstUseExpr = nullptr;
          } else if (FD && FD->getName() == "realloc") {
            PtrState &St = States[LHS];
            St.Allocated = true;
            St.Checked = false;
            St.Used = false;
            St.AllocExpr = BO;
            St.FirstUseExpr = nullptr;
          }
        }
      }
    }

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      const Expr *Cond = IfS->getCond();
      for (auto &KV : States) {
        if (KV.second.Allocated && !KV.second.Checked &&
            isDirectNullCheck(Cond, KV.first)) {
          KV.second.Checked = true;
        }
      }
    }

    for (auto &KV : States) {
      if (!KV.second.Allocated || KV.second.Checked || KV.second.Used)
        continue;
      if (const Stmt *Use = findDirectUse(S, KV.first)) {
        KV.second.Used = true;
        KV.second.FirstUseExpr = dyn_cast<Expr>(Use);
        emitASTReport(Use, ADC, BR);
        Reported = true;
        return;
      }
    }

    for (const Stmt *Child : S->children())
      handleStmt(Child, ADC, BR, States, Reported);
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

    llvm::DenseMap<const VarDecl *, PtrState> States;
    bool Reported = false;
    handleStmt(FD->getBody(), ADC, BR, States, Reported);
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