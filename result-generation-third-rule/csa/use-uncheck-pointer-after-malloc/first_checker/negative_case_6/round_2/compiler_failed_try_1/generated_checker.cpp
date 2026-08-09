#include <memory>
#include <optional>
#include <utility>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/Basic/LLVM.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

struct PointerInfo {
  bool Allocated = false;
  bool Checked = false;
  bool Used = false;
  bool Reallocated = false;
  bool Reported = false;
  SourceLocation AllocLoc;
  SourceLocation ReallocLoc;
  SourceLocation FirstUseLoc;
};

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static const VarDecl *getBaseVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return dyn_cast<VarDecl>(ME->getMemberDecl());
    return nullptr;
  }

  static const VarDecl *getPointerVarFromLValue(const Expr *E) {
    return getBaseVarFromExpr(E);
  }

  static const VarDecl *getPointerVarFromValueExpr(const Expr *E) {
    return getBaseVarFromExpr(E);
  }

  static bool isNullLikeExpr(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();

    if (isa<CXXNullPtrLiteralExpr>(E))
      return true;

    if (const auto *IL = dyn_cast<IntegerLiteral>(E))
      return IL->getValue().isZero();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      const auto *VD = dyn_cast<VarDecl>(DRE->getDecl());
      if (!VD)
        return false;
      if (VD->getName() == "NULL") {
        if (const Expr *Init = VD->getInit())
          return isNullLikeExpr(Init);
      }
    }

    return false;
  }

  static bool isUseSite(const Expr *E) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    return isa<ArraySubscriptExpr>(E) || isa<UnaryOperator>(E) ||
           isa<MemberExpr>(E) || isa<CallExpr>(E) || isa<CXXOperatorCallExpr>(E) ||
           isa<BinaryOperator>(E) || isa<ImplicitCastExpr>(E) ||
           isa<DeclRefExpr>(E);
  }

  static bool isAssignmentToPtr(const BinaryOperator *BO, const VarDecl *V) {
    if (!BO || !BO->isAssignmentOp())
      return false;
    return getPointerVarFromLValue(BO->getLHS()) == V;
  }

  static bool isMallocLikeCall(const CallExpr *CE) {
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const Expr *strip(const Expr *E) {
    return E ? E->IgnoreParenImpCasts() : nullptr;
  }

  static const VarDecl *getCheckedVarFromCondition(const Expr *Cond) {
    Cond = strip(Cond);
    if (!Cond)
      return nullptr;

    if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
      if (UO->getOpcode() == UO_LNot)
        return getPointerVarFromValueExpr(UO->getSubExpr());
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
      const Expr *L = strip(BO->getLHS());
      const Expr *R = strip(BO->getRHS());
      if (isNullLikeExpr(L))
        return getPointerVarFromValueExpr(R);
      if (isNullLikeExpr(R))
        return getPointerVarFromValueExpr(L);
    }

    return getPointerVarFromValueExpr(Cond);
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

  void markAllocation(PointerInfo &Info, const Expr *Init, bool IsRealloc) const {
    Info.Allocated = true;
    Info.Checked = false;
    Info.Used = false;
    Info.Reported = false;
    Info.Reallocated = IsRealloc;
    if (Init)
      Info.AllocLoc = Init->getBeginLoc();
    if (IsRealloc && Init)
      Info.ReallocLoc = Init->getBeginLoc();
  }

  void analyzeStmt(const Stmt *S, llvm::DenseMap<const VarDecl *, PointerInfo> &State,
                   AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;
        const Expr *Init = VD->getInit();
        if (!Init)
          continue;
        Init = strip(Init);
        if (const auto *CE = dyn_cast<CallExpr>(Init)) {
          if (!isMallocLikeCall(CE))
            continue;
          auto &Info = State[VD];
          markAllocation(Info, CE, false);
        }
      }
      return;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        const VarDecl *LHSVar = getPointerVarFromLValue(BO->getLHS());
        const Expr *RHS = strip(BO->getRHS());
        if (!LHSVar || !RHS)
          return;
        if (const auto *CE = dyn_cast<CallExpr>(RHS)) {
          if (isMallocLikeCall(CE)) {
            auto &Info = State[LHSVar];
            markAllocation(Info, CE, true);
          }
        }
        return;
      }

      if (BO->isLogicalOp() || BO->isRelationalOp()) {
        if (const VarDecl *V = getCheckedVarFromCondition(BO)) {
          auto It = State.find(V);
          if (It != State.end() && It->second.Allocated)
            It->second.Checked = true;
        }
      }
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(S)) {
      if (UO->getOpcode() == UO_LNot) {
        if (const VarDecl *V = getCheckedVarFromCondition(UO)) {
          auto It = State.find(V);
          if (It != State.end() && It->second.Allocated)
            It->second.Checked = true;
        }
      }
    }

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      for (const Expr *Arg : CE->arguments()) {
        const VarDecl *V = getPointerVarFromValueExpr(Arg);
        if (!V)
          continue;
        auto It = State.find(V);
        if (It == State.end())
          continue;
        PointerInfo &Info = It->second;
        if (!Info.Allocated || Info.Reported)
          continue;
        Info.Used = true;
        if (!Info.Checked) {
          Info.Reported = true;
          Info.FirstUseLoc = Arg->getBeginLoc();
          emitASTReport(Arg, ADC, BR);
        }
      }
      return;
    }

    for (const Stmt *Child : S->children())
      analyzeStmt(Child, State, ADC, BR);

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(S)) {
      const VarDecl *V = getPointerVarFromValueExpr(ASE->getBase());
      if (!V)
        return;
      auto It = State.find(V);
      if (It == State.end())
        return;
      PointerInfo &Info = It->second;
      if (!Info.Allocated || Info.Reported)
        return;
      Info.Used = true;
      if (!Info.Checked) {
        Info.Reported = true;
        Info.FirstUseLoc = ASE->getBeginLoc();
        emitASTReport(ASE, ADC, BR);
      }
      return;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(S)) {
      const VarDecl *V = getPointerVarFromValueExpr(ME->getBase());
      if (!V)
        return;
      auto It = State.find(V);
      if (It == State.end())
        return;
      PointerInfo &Info = It->second;
      if (!Info.Allocated || Info.Reported)
        return;
      Info.Used = true;
      if (!Info.Checked) {
        Info.Reported = true;
        Info.FirstUseLoc = ME->getBeginLoc();
        emitASTReport(ME, ADC, BR);
      }
      return;
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(S)) {
      const auto *V = dyn_cast<VarDecl>(DRE->getDecl());
      if (!V)
        return;
      auto It = State.find(V);
      if (It == State.end())
        return;
      PointerInfo &Info = It->second;
      if (!Info.Allocated || Info.Reported)
        return;
      if (isUseSite(DRE)) {
        Info.Used = true;
        if (!Info.Checked) {
          Info.Reported = true;
          Info.FirstUseLoc = DRE->getBeginLoc();
          emitASTReport(DRE, ADC, BR);
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
    if (!ADC)
      return;

    llvm::DenseMap<const VarDecl *, PointerInfo> State;
    analyzeStmt(FD->getBody(), State, ADC, BR);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;