I’m fixing the type mismatch in the checker itself, keeping the class and registration names intact, and I’ll verify the resulting implementation stays in the ASTCodeBody pattern the repo expects.I’m reading just enough of the existing file shape to patch the bad assignments without disturbing the rest of the plugin surface.```cpp
#include <memory>
#include <optional>
#include <vector>

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

  struct AllocInfo {
    const VarDecl *VD = nullptr;
    bool IsGlobal = false;
    const Expr *AllocExpr = nullptr;
    const Stmt *FirstUse = nullptr;
    bool Checked = false;
    bool Violated = false;
  };

  static const VarDecl *getDirectVarDecl(const Expr *E) {
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());

    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return dyn_cast<VarDecl>(ME->getMemberDecl());

    return nullptr;
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

  static bool isNullLiteral(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E) ||
           (isa<ImplicitCastExpr>(E) && E->getType()->isNullPtrType());
  }

  static bool exprUsesVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return DRE->getDecl() == VD;
    for (const Stmt *Child : E->children()) {
      const auto *CE = dyn_cast_or_null<Expr>(Child);
      if (exprUsesVar(CE, VD))
        return true;
    }
    return false;
  }

  static bool containsDereferenceOfVar(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(S)) {
      if (UO->getOpcode() == UO_Deref && exprUsesVar(UO->getSubExpr(), VD))
        return true;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(S)) {
      if (exprUsesVar(ME->getBase(), VD))
        return true;
    }

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      for (const Expr *Arg : CE->arguments())
        if (exprUsesVar(Arg, VD))
          return true;
    }

    for (const Stmt *Child : S->children())
      if (containsDereferenceOfVar(Child, VD))
        return true;

    return false;
  }

  static bool isNullCheckCondition(const Expr *Cond, const VarDecl *VD) {
    if (!Cond || !VD)
      return false;

    Cond = Cond->IgnoreParenImpCasts();

    if (exprUsesVar(Cond, VD))
      return true;

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      if (!BO->isEqualityOp() && !BO->isRelationalOp())
        return false;
      return (exprUsesVar(BO->getLHS(), VD) && isNullLiteral(BO->getRHS())) ||
             (exprUsesVar(BO->getRHS(), VD) && isNullLiteral(BO->getLHS()));
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond))
      return UO->getOpcode() == UO_LNot && exprUsesVar(UO->getSubExpr(), VD);

    return false;
  }

  static const Stmt *findFirstUse(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return nullptr;

    if (containsDereferenceOfVar(S, VD))
      return S;

    for (const Stmt *Child : S->children()) {
      if (const Stmt *Found = findFirstUse(Child, VD))
        return Found;
    }
    return nullptr;
  }

  void emitReport(const Stmt *Violation, const Decl *D, BugReporter &BR) const {
    if (!Violation)
      return;
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(D);
    BR.emitReport(std::move(Report));
  }

  void scanStmt(const Stmt *S, const Decl *D, BugReporter &BR,
                std::vector<AllocInfo> &Tracked) const {
    if (!S)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
        const Expr *RHS = BO->getRHS();
        if (const VarDecl *VD = getDirectVarDecl(LHS)) {
          if (const auto *RHSCall = dyn_cast<CallExpr>(RHS->IgnoreParenImpCasts());
              isAllocationCall(RHSCall)) {
            AllocInfo *Info = nullptr;
            for (auto &T : Tracked)
              if (T.VD == VD)
                Info = &T;
            if (!Info)
              Info = &Tracked.emplace_back();
            Info->VD = VD;
            Info->IsGlobal = VD->hasGlobalStorage();
            Info->AllocExpr = RHSCall;
            Info->Checked = false;
            Info->Violated = false;
            Info->FirstUse = nullptr;
            return;
          }

          for (auto &T : Tracked) {
            if (T.VD == VD && !T.Checked && !T.Violated &&
                containsDereferenceOfVar(RHS, VD)) {
              T.FirstUse = S;
              T.Violated = true;
              emitReport(S, D, BR);
              return;
            }
          }
        }
      }
    }

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      if (isAllocationCall(CE) && !CE->arguments().empty()) {
        const Expr *Assigned = nullptr;
        if (const auto *Bin = dyn_cast<BinaryOperator>(S))
          if (Bin->isAssignmentOp())
            Assigned = Bin->getLHS();

        if (Assigned) {
          if (const VarDecl *VD = getDirectVarDecl(Assigned)) {
            AllocInfo &Info = Tracked.emplace_back();
            Info.VD = VD;
            Info.IsGlobal = VD->hasGlobalStorage();
            Info.AllocExpr = CE;
            return;
          }
        }
      }
    }

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      const Expr *Cond = If->getCond();
      for (auto &T : Tracked) {
        if (T.VD && !T.Checked && isNullCheckCondition(Cond, T.VD))
          T.Checked = true;
      }
    }

    for (auto &T : Tracked) {
      if (T.VD && !T.Checked && !T.Violated &&
          containsDereferenceOfVar(S, T.VD)) {
        T.FirstUse = S;
        T.Violated = true;
        emitReport(S, D, BR);
        return;
      }
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, D, BR, Tracked);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    std::vector<AllocInfo> Tracked;
    scanStmt(FD->getBody(), D, BR, Tracked);
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