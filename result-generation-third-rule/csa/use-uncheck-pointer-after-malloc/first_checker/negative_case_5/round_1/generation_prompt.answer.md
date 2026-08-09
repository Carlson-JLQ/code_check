I’m reading the existing checker template and the available CSA APIs, then I’ll fill in the path-sensitive tracking for allocation, null-check, and first-use reporting in a single C++ file.```cpp
#include <algorithm>
#include <memory>
#include <utility>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/SVals.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

struct PointerTracker {
  const MemRegion *Region = nullptr;
  const VarDecl *VD = nullptr;
  bool Checked = false;
  bool Reported = false;
  bool AllocSeen = false;
  SourceLocation AllocLoc;
  SourceLocation FirstUseLoc;
};

struct PointerTrackerMap {};
using PointerTrackerMapTy = llvm::ImmutableMap<const MemRegion *, PointerTracker>;

template <>
struct ProgramStateTrait<PointerTrackerMap>
    : public ProgramStatePartialTrait<PointerTrackerMapTy> {
  static void *GDMIndex() { static int Index; return &Index; }
};

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  static bool isNullConstant(const Expr *E, ASTContext &Ctx) {
    if (!E)
      return false;
    Expr::EvalResult Result;
    if (!E->EvaluateAsInt(Result, Ctx))
      return false;
    return Result.Val.getInt().isZero();
  }

  static const DeclRefExpr *getDeclRefExpr(const Expr *E) {
    E = E ? E->IgnoreParenImpCasts() : nullptr;
    return dyn_cast_or_null<DeclRefExpr>(E);
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    if (const auto *DRE = getDeclRefExpr(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static const MemberExpr *getMemberExpr(const Expr *E) {
    E = E ? E->IgnoreParenImpCasts() : nullptr;
    return dyn_cast_or_null<MemberExpr>(E);
  }

  static const MemRegion *getAccessedRegion(const Expr *E, ProgramStateRef State,
                                            CheckerContext &C) {
    if (!E)
      return nullptr;
    SVal V = C.getSVal(E);
    if (const MemRegion *R = V.getAsRegion())
      return R;
    if (const auto *ME = getMemberExpr(E)) {
      if (const VarDecl *VD = dyn_cast<VarDecl>(ME->getMemberDecl())) {
        SVal Base = C.getSVal(ME->getBase());
        if (const MemRegion *BR = Base.getAsRegion())
          return State->getStateManager().getRegionManager().getFieldRegion(
              VD->getType(), BR, VD);
      }
    }
    return nullptr;
  }

  static bool isAllocationCall(const CallExpr *CE) {
    if (!CE)
      return false;
    if (const FunctionDecl *FD = CE->getDirectCallee()) {
      IdentifierInfo *II = FD->getIdentifier();
      if (!II)
        return false;
      StringRef Name = II->getName();
      return Name == "malloc" || Name == "calloc" || Name == "realloc";
    }
    return false;
  }

  static const Expr *getAllocationArgExpr(const CallExpr *CE) {
    return CE && CE->getNumArgs() ? CE->getArg(0) : nullptr;
  }

  void reportViolation(const PointerTracker &T, const Expr *ViolationExpr,
                       CheckerContext &C) const {
    if (T.Reported)
      return;

    const Stmt *LocStmt = ViolationExpr ? ViolationExpr : nullptr;
    PathDiagnosticLocation Location(
        LocStmt ? LocStmt->getBeginLoc() : T.FirstUseLoc, C.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    if (LocStmt)
      Report->addRange(LocStmt->getSourceRange());
    C.emitReport(std::move(Report));
  }

  PointerTrackerMapTy setTracker(ProgramStateRef State, const MemRegion *R,
                                 const PointerTracker &T) const {
    return State->set<PointerTrackerMap>(State->get<PointerTrackerMap>().set(R, T));
  }

  ProgramStateRef addAllocation(ProgramStateRef State, const MemRegion *R,
                                const VarDecl *VD, SourceLocation Loc) const {
    PointerTracker T;
    T.Region = R;
    T.VD = VD;
    T.AllocSeen = true;
    T.AllocLoc = Loc;
    return State->set<PointerTrackerMap>(State->get<PointerTrackerMap>().set(R, T));
  }

  ProgramStateRef markChecked(ProgramStateRef State, const MemRegion *R) const {
    PointerTrackerMapTy M = State->get<PointerTrackerMap>();
    if (const PointerTracker *T = M.lookup(R)) {
      PointerTracker NT = *T;
      NT.Checked = true;
      State = State->set<PointerTrackerMap>(M.set(R, NT));
    }
    return State;
  }

  ProgramStateRef markUse(ProgramStateRef State, const MemRegion *R,
                          SourceLocation Loc) const {
    PointerTrackerMapTy M = State->get<PointerTrackerMap>();
    if (const PointerTracker *T = M.lookup(R)) {
      PointerTracker NT = *T;
      NT.FirstUseLoc = NT.FirstUseLoc.isValid() ? NT.FirstUseLoc : Loc;
      State = State->set<PointerTrackerMap>(M.set(R, NT));
    }
    return State;
  }

  bool handlePossibleNullCheck(const BinaryOperator *BO, CheckerContext &C) const {
    if (!BO || !BO->isComparisonOp())
      return false;
    const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
    const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
    const VarDecl *VD = getReferencedVar(LHS);
    if (!VD)
      VD = getReferencedVar(RHS);
    if (!VD)
      return false;
    if (!isNullConstant(LHS, C.getASTContext()) &&
        !isNullConstant(RHS, C.getASTContext()))
      return false;

    const MemRegion *R = getAccessedRegion(VD->getAnyInitializer()
                                               ? VD->getAnyInitializer()
                                               : nullptr,
                                           C.getState(), C);
    if (!R) {
      SVal V = C.getSVal(VD);
      R = V.getAsRegion();
    }
    if (!R)
      return false;

    C.addTransition(markChecked(C.getState(), R));
    return true;
  }

  void scanExprForEvents(const Expr *E, CheckerContext &C) const {
    if (!E)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(E->IgnoreParenImpCasts())) {
      if (handlePossibleNullCheck(BO, C))
        return;
    }

    if (const auto *Call = dyn_cast<CallExpr>(E->IgnoreParenImpCasts())) {
      if (isAllocationCall(Call)) {
        if (const Expr *Arg = getAllocationArgExpr(Call)) {
          if (const VarDecl *VD = getReferencedVar(Arg)) {
            const MemRegion *R = C.getSVal(VD).getAsRegion();
            if (R) {
              ProgramStateRef State = addAllocation(C.getState(), R, VD, Call->getBeginLoc());
              C.addTransition(State);
            }
          }
        }
        return;
      }
    }

    if (const VarDecl *VD = getReferencedVar(E)) {
      const MemRegion *R = C.getSVal(VD).getAsRegion();
      if (!R)
        return;

      ProgramStateRef State = C.getState();
      PointerTrackerMapTy M = State->get<PointerTrackerMap>();
      if (const PointerTracker *T = M.lookup(R)) {
        if (T->AllocSeen && !T->Checked && !T->Reported) {
          PointerTracker NT = *T;
          NT.Reported = true;
          NT.FirstUseLoc = E->getBeginLoc();
          State = State->set<PointerTrackerMap>(M.set(R, NT));
          C.addTransition(State);
          reportViolation(NT, E, C);
        } else {
          C.addTransition(markUse(State, R, E->getBeginLoc()));
        }
      }
    }

    for (const Stmt *Child : E->children()) {
      if (const auto *ChildExpr = dyn_cast_or_null<Expr>(Child))
        scanExprForEvents(ChildExpr, C);
    }
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;
    if (!D)
      return;
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    struct Walker {
      const GeneratedUseUncheckPointerAfterMallocChecker *Checker;
      CheckerContext *Ctx;
      void walk(const Stmt *S) const {
        if (!S)
          return;
        if (const auto *E = dyn_cast<Expr>(S))
          Checker->scanExprForEvents(E, *Ctx);
        for (const Stmt *Child : S->children())
          walk(Child);
      }
    };

    ExplodedNode *N = nullptr;
    CheckerContext Ctx(BR, N, AM.getAnalysisManager(), nullptr);
    Walker{this, &Ctx}.walk(Body);
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