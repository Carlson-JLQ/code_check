#include <memory>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

struct VarInfo {
  const VarDecl *VD = nullptr;
  const Expr *AllocExpr = nullptr;
  unsigned FirstUseIndex = 0;
  bool Checked = false;
  bool Used = false;
  bool Violated = false;
};

static const Expr *stripCasts(const Expr *E) {
  if (!E)
    return nullptr;
  E = E->IgnoreParenImpCasts();
  return E;
}

static const VarDecl *getReferencedVar(const Expr *E) {
  E = stripCasts(E);
  if (!E)
    return nullptr;
  if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
    return dyn_cast<VarDecl>(DRE->getDecl());
  return nullptr;
}

static bool isNullLiteralExpr(const Expr *E) {
  if (!E)
    return false;
  E = E->IgnoreParenImpCasts();
  if (isa<CXXNullPtrLiteralExpr>(E))
    return true;
  if (const auto *IL = dyn_cast<IntegerLiteral>(E))
    return IL->getValue().isZero();
  return false;
}

static bool isAllocatorName(StringRef Name) {
  return Name == "malloc" || Name == "calloc" || Name == "realloc";
}

static const CallExpr *asCall(const Expr *E) {
  E = stripCasts(E);
  return dyn_cast_or_null<CallExpr>(E);
}

static bool isAllocationCall(const Expr *E) {
  const CallExpr *CE = asCall(E);
  if (!CE)
    return false;
  const FunctionDecl *FD = CE->getDirectCallee();
  if (!FD)
    return false;
  return isAllocatorName(FD->getName());
}

static bool isSimpleNullCheck(const Expr *Cond, const VarDecl *VD) {
  Cond = Cond ? Cond->IgnoreParenImpCasts() : nullptr;
  if (!Cond || !VD)
    return false;

  if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
    if (UO->getOpcode() == UO_LNot)
      return getReferencedVar(UO->getSubExpr()) == VD;
  }

  if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
    if (!(BO->isRelationalOp() || BO->isEqualityOp()))
      return false;
    const Expr *L = BO->getLHS()->IgnoreParenImpCasts();
    const Expr *R = BO->getRHS()->IgnoreParenImpCasts();
    return (getReferencedVar(L) == VD && isNullLiteralExpr(R)) ||
           (getReferencedVar(R) == VD && isNullLiteralExpr(L));
  }

  return getReferencedVar(Cond) == VD;
}

static void collectUses(const Stmt *S, const VarDecl *VD,
                        std::vector<const Expr *> &Uses) {
  if (!S)
    return;

  if (const auto *E = dyn_cast<Expr>(S)) {
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E->IgnoreParenImpCasts())) {
      if (dyn_cast<VarDecl>(DRE->getDecl()) == VD)
        Uses.push_back(E);
    }
  }

  for (const Stmt *Child : S->children())
    collectUses(Child, VD, Uses);
}

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  void emitASTReport(const Expr *Violation, AnalysisDeclContext *ADC,
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

  bool isCheckStatementForVar(const Stmt *S, const VarDecl *VD) const {
    if (!S || !VD)
      return false;

    if (const auto *If = dyn_cast<IfStmt>(S))
      return isSimpleNullCheck(If->getCond(), VD);

    if (const auto *While = dyn_cast<WhileStmt>(S))
      return isSimpleNullCheck(While->getCond(), VD);

    if (const auto *Do = dyn_cast<DoStmt>(S))
      return isSimpleNullCheck(Do->getCond(), VD);

    if (const auto *For = dyn_cast<ForStmt>(S))
      return isSimpleNullCheck(For->getCond(), VD);

    if (const auto *Swt = dyn_cast<SwitchStmt>(S))
      return isSimpleNullCheck(Swt->getCond(), VD);

    return false;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    const Stmt *Body = FD->getBody();
    if (!Body || !ADC)
      return;

    std::vector<const Stmt *> TopLevel;
    if (const auto *CS = dyn_cast<CompoundStmt>(Body)) {
      for (const Stmt *S : CS->body())
        TopLevel.push_back(S);
    } else {
      TopLevel.push_back(Body);
    }

    std::vector<VarInfo> Vars;
    std::set<const VarDecl *> Reported;

    auto noteAllocation = [&](const VarDecl *VD, const Expr *AllocExpr) {
      if (!VD || !AllocExpr)
        return;
      for (auto &V : Vars) {
        if (V.VD == VD) {
          V.AllocExpr = AllocExpr;
          V.Checked = false;
          V.Used = false;
          V.Violated = false;
          V.FirstUseIndex = 0;
          return;
        }
      }
      VarInfo VI;
      VI.VD = VD;
      VI.AllocExpr = AllocExpr;
      Vars.push_back(VI);
    };

    for (unsigned I = 0; I < TopLevel.size(); ++I) {
      const Stmt *S = TopLevel[I];

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *D2 : DS->decls()) {
          const auto *VD = dyn_cast<VarDecl>(D2);
          if (!VD)
            continue;
          const Expr *Init = VD->getInit();
          if (isAllocationCall(Init))
            noteAllocation(VD, Init);
        }
      }

      for (auto &V : Vars) {
        if (!V.VD || V.Violated)
          continue;

        if (isCheckStatementForVar(S, V.VD)) {
          V.Checked = true;
          continue;
        }

        std::vector<const Expr *> Uses;
        collectUses(S, V.VD, Uses);
        if (Uses.empty())
          continue;

        V.Used = true;
        if (!V.Checked) {
          V.Violated = true;
          V.FirstUseIndex = I;
          if (Reported.insert(V.VD).second)
            emitASTReport(Uses.front(), ADC, BR);
        }
      }

      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *D2 : DS->decls()) {
          const auto *VD = dyn_cast<VarDecl>(D2);
          if (!VD)
            continue;
          const Expr *Init = VD->getInit();
          if (isAllocationCall(Init))
            noteAllocation(VD, Init);
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
        if (BO->isAssignmentOp()) {
          const VarDecl *LHSVar = getReferencedVar(BO->getLHS());
          if (LHSVar && isAllocationCall(BO->getRHS()))
            noteAllocation(LHSVar, BO->getRHS());
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