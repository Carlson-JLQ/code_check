I’m reading the available analyzer APIs and the supplied template first, then I’ll wire the checker into the AST callback with a minimal state machine for allocation, check, use, and realloc.```cpp
#include <memory>
#include <optional>
#include <utility>

#include "clang/AST/Expr.h"
#include "clang/AST/OperationKinds.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Type.h"
#include "clang/AST/Decl.h"
#include "clang/Basic/SourceManager.h"
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
    const VarDecl *VD = nullptr;
    bool Allocated = false;
    bool Checked = false;
    bool Used = false;
    bool Reported = false;
    bool SeenRealloc = false;
    SourceLocation AllocLoc;
    SourceLocation FirstUseLoc;
  };

  static const VarDecl *getBaseVar(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static bool isNullLiteral(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return isa<CXXNullPtrLiteralExpr>(E) ||
           (isa<IntegerLiteral>(E) && E->getBeginLoc().isValid() &&
            E->getType()->isIntegerType());
  }

  static bool isAllocFunction(const FunctionDecl *FD) {
    if (!FD)
      return false;
    StringRef N = FD->getName();
    return N == "malloc" || N == "calloc" || N == "realloc";
  }

  static bool isPointerType(const QualType QT) { return QT->isPointerType(); }

  static bool exprUsesVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;

    for (const Stmt *Child : E->children()) {
      if (const auto *CE = dyn_cast_or_null<Expr>(Child))
        if (exprUsesVar(CE, VD))
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
        return exprUsesVar(UO->getSubExpr(), VD);
      return false;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isComparisonOp())
        return false;
      const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
      return (exprUsesVar(L, VD) && isNullLiteral(R)) ||
             (exprUsesVar(R, VD) && isNullLiteral(L));
    }

    return exprUsesVar(Cond, VD);
  }

  static const Expr *findFirstUseExpr(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return nullptr;

    if (const auto *E = dyn_cast<Expr>(S)) {
      const Expr *IE = E->IgnoreParenImpCasts();

      if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(IE)) {
        if (exprUsesVar(ASE->getBase(), VD) || exprUsesVar(ASE->getIdx(), VD))
          return E;
      }

      if (const auto *UO = dyn_cast<UnaryOperator>(IE)) {
        if ((UO->getOpcode() == UO_Deref || UO->getOpcode() == UO_AddrOf) &&
            exprUsesVar(UO->getSubExpr(), VD))
          return E;
      }

      if (const auto *ME = dyn_cast<MemberExpr>(IE)) {
        if (exprUsesVar(ME->getBase(), VD))
          return E;
      }

      if (const auto *CE = dyn_cast<CallExpr>(IE)) {
        for (const Expr *Arg : CE->arguments())
          if (exprUsesVar(Arg, VD))
            return E;
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(IE)) {
        if (exprUsesVar(BO->getLHS(), VD) || exprUsesVar(BO->getRHS(), VD))
          return E;
      }

      if (const auto *DRE = dyn_cast<DeclRefExpr>(IE)) {
        if (DRE->getDecl() == VD)
          return E;
      }
    }

    for (const Stmt *Child : S->children()) {
      if (const auto *CS = dyn_cast_or_null<Stmt>(Child))
        if (const Expr *Found = findFirstUseExpr(CS, VD))
          return Found;
    }
    return nullptr;
  }

  static void collectPointerVars(
      const Stmt *S, llvm::SmallVectorImpl<const VarDecl *> &Out) {
    if (!S)
      return;
    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        if (const auto *VD = dyn_cast<VarDecl>(D))
          if (isPointerType(VD->getType()))
            Out.push_back(VD);
      }
    }
    for (const Stmt *Child : S->children())
      collectPointerVars(Child, Out);
  }

  static const Expr *getInitExpr(const VarDecl *VD) {
    if (!VD || !VD->hasInit())
      return nullptr;
    return VD->getInit();
  }

  void reportUse(const Expr *Use, AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!Use || !ADC)
      return;
    PathDiagnosticLocation Location(Use->getBeginLoc(), BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Use->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void scanStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                llvm::DenseMap<const VarDecl *, PtrState> &States) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !isPointerType(VD->getType()))
          continue;
        PtrState &PS = States[VD];
        PS.VD = VD;
        const Expr *Init = getInitExpr(VD);
        if (!Init)
          continue;
        Init = Init->IgnoreParenImpCasts();
        if (const auto *CE = dyn_cast<CallExpr>(Init)) {
          const auto *FD = CE->getDirectCallee();
          if (isAllocFunction(FD)) {
            PS.Allocated = true;
            PS.Checked = false;
            PS.Used = false;
            PS.Reported = false;
            PS.SeenRealloc = (FD->getName() == "realloc");
            PS.AllocLoc = Init->getBeginLoc();
          }
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getBaseVar(BO->getLHS());
        const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
        if (VD && isPointerType(VD->getType())) {
          PtrState &PS = States[VD];
          PS.VD = VD;
          if (const auto *CE = dyn_cast<CallExpr>(RHS)) {
            const auto *FD = CE->getDirectCallee();
            if (isAllocFunction(FD)) {
              PS.Allocated = true;
              PS.Checked = false;
              PS.Used = false;
              PS.Reported = false;
              PS.SeenRealloc = (FD->getName() == "realloc");
              PS.AllocLoc = RHS->getBeginLoc();
            }
          }
        }
      }
    }

    if (const auto *IF = dyn_cast<IfStmt>(S)) {
      if (const auto *Cond = IF->getCond()) {
        for (auto &It : States) {
          PtrState &PS = It.second;
          if (PS.Allocated && !PS.Reported && isNullCheckCondition(Cond, PS.VD))
            PS.Checked = true;
        }
      }
    }

    for (auto &It : States) {
      PtrState &PS = It.second;
      if (!PS.VD || !PS.Allocated || PS.Reported)
        continue;
      const Expr *Use = findFirstUseExpr(S, PS.VD);
      if (Use) {
        PS.Used = true;
        PS.Reported = !PS.Checked;
        if (PS.Reported)
          reportUse(Use, ADC, BR);
      }
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, ADC, BR, States);
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
    scanStmt(FD->getBody(), ADC, BR, States);
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