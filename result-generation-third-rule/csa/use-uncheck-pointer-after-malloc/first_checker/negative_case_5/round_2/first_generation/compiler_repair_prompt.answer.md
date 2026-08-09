I’m patching the checker in place: fix the two compile errors, keep the existing class and registration names, and avoid changing the report shape. Then I’ll give you the standalone C++ file only.I’ve confirmed the breakage is localized to two helper/API mismatches. I’m adjusting the AST traversal so statement nodes are only handed to expression helpers after a safe cast, and I’m replacing the nonexistent `ASTContext::getDummy()` call with a direct null-constant test that doesn’t depend on that API.```cpp
#include <algorithm>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
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
struct TrackedVar {
  const VarDecl *VD = nullptr;
  bool Allocated = false;
  bool Reallocated = false;
  bool Checked = false;
  bool UsedSinceAllocOrRealloc = false;
  bool Reported = false;
  SourceLocation LastAllocLoc;
};

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static bool isAllocationFunc(const FunctionDecl *FD) {
    if (!FD)
      return false;
    IdentifierInfo *II = FD->getIdentifier();
    if (!II)
      return false;
    StringRef Name = II->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const Expr *ignoreParenImpCasts(const Expr *E) {
    return E ? E->IgnoreParenImpCasts() : nullptr;
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    E = ignoreParenImpCasts(E);
    if (!E)
      return nullptr;
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
        return VD;
    }
    return nullptr;
  }

  static const VarDecl *getAssignedVar(const Stmt *S) {
    const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
    if (!BO || !BO->isAssignmentOp())
      return nullptr;
    return getReferencedVar(BO->getLHS());
  }

  static const CallExpr *getAllocCallFromExpr(const Expr *E) {
    E = ignoreParenImpCasts(E);
    if (!E)
      return nullptr;
    return dyn_cast<CallExpr>(E);
  }

  static bool isNullConstant(const Expr *E) {
    E = ignoreParenImpCasts(E);
    if (!E)
      return false;
    return isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E);
  }

  static bool isNullCheckExpr(const Expr *E, const VarDecl *VD) {
    E = ignoreParenImpCasts(E);
    if (!E || !VD)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_LNot)
        return getReferencedVar(UO->getSubExpr()) == VD;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isEqualityOp())
        return false;
      const VarDecl *L = getReferencedVar(BO->getLHS());
      const VarDecl *R = getReferencedVar(BO->getRHS());
      if ((L == VD && isNullConstant(BO->getRHS())) ||
          (R == VD && isNullConstant(BO->getLHS())))
        return true;
      return false;
    }

    return getReferencedVar(E) == VD;
  }

  static bool exprUsesVar(const Expr *E, const VarDecl *VD) {
    if (!E || !VD)
      return false;
    E = E->IgnoreParenImpCasts();
    if (!E)
      return false;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == VD;

    for (const Stmt *Child : E->children()) {
      if (const auto *CE = dyn_cast_or_null<Expr>(Child))
        if (exprUsesVar(CE, VD))
          return true;
    }
    return false;
  }

  static bool stmtUsesVar(const Stmt *S, const VarDecl *VD) {
    if (!S || !VD)
      return false;
    if (const auto *E = dyn_cast<Expr>(S))
      return exprUsesVar(E, VD);
    for (const Stmt *Child : S->children()) {
      if (stmtUsesVar(Child, VD))
        return true;
    }
    return false;
  }

  void emitReport(const VarDecl *VD, const Stmt *S, AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    if (!VD || !S || !ADC)
      return;
    SourceLocation L = S->getBeginLoc();
    PathDiagnosticLocation Location(L, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(S->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void handleStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                  std::vector<TrackedVar> &Vars) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD || !VD->hasInit())
          continue;
        const CallExpr *CE = getAllocCallFromExpr(VD->getInit());
        if (!CE)
          continue;
        const auto *FD = CE->getDirectCallee();
        if (!isAllocationFunc(FD))
          continue;
        auto It = std::find_if(Vars.begin(), Vars.end(),
                               [&](const TrackedVar &TV) { return TV.VD == VD; });
        if (It == Vars.end()) {
          Vars.push_back({VD, true, false, false, false, false, CE->getBeginLoc()});
        } else {
          It->Allocated = true;
          It->Reallocated = false;
          It->Checked = false;
          It->UsedSinceAllocOrRealloc = false;
          It->Reported = false;
          It->LastAllocLoc = CE->getBeginLoc();
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *VD = getAssignedVar(S);
        const CallExpr *CE = getAllocCallFromExpr(BO->getRHS());
        if (VD && CE && isAllocationFunc(CE->getDirectCallee())) {
          auto It = std::find_if(Vars.begin(), Vars.end(),
                                 [&](const TrackedVar &TV) { return TV.VD == VD; });
          if (It == Vars.end()) {
            Vars.push_back({VD, true, true, false, false, false,
                            CE->getBeginLoc()});
          } else {
            It->Allocated = true;
            It->Reallocated = true;
            It->Checked = false;
            It->UsedSinceAllocOrRealloc = false;
            It->Reported = false;
            It->LastAllocLoc = CE->getBeginLoc();
          }
        }
      } else if (BO->isLogicalOp() || BO->isEqualityOp() || BO->isRelationalOp()) {
        for (auto &TV : Vars) {
          if (!TV.Allocated || TV.Reported)
            continue;
          if (isNullCheckExpr(BO, TV.VD))
            TV.Checked = true;
        }
      }
    }

    for (auto &TV : Vars) {
      if (!TV.Allocated || TV.Reported || TV.Checked)
        continue;
      if (stmtUsesVar(S, TV.VD)) {
        TV.UsedSinceAllocOrRealloc = true;
        TV.Reported = true;
        emitReport(TV.VD, S, ADC, BR);
        break;
      }
    }

    for (const Stmt *Child : S->children())
      handleStmt(Child, ADC, BR, Vars);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    std::vector<TrackedVar> Vars;
    handleStmt(FD->getBody(), AM.getAnalysisDeclContext(D), BR, Vars);
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