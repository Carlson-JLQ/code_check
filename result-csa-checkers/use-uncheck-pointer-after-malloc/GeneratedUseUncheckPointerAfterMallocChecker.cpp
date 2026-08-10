#include <cstdint>
#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/ExprCXX.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/Hashing.h"

using namespace clang;
using namespace ento;

namespace {
class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  enum class VarState { Unchecked, Checked, Warned };

  struct PointerSlot {
    const VarDecl *VD = nullptr;
    const FieldDecl *FD = nullptr;

    PointerSlot() = default;
    PointerSlot(const VarDecl *VD, const FieldDecl *FD = nullptr)
        : VD(VD), FD(FD) {}

    bool isValid() const { return VD != nullptr; }

    friend bool operator==(const PointerSlot &L, const PointerSlot &R) {
      return L.VD == R.VD && L.FD == R.FD;
    }
  };

  struct PointerSlotDenseMapInfo {
    static PointerSlot getEmptyKey() {
      return PointerSlot(
          reinterpret_cast<const VarDecl *>(static_cast<uintptr_t>(-1)),
          reinterpret_cast<const FieldDecl *>(static_cast<uintptr_t>(-1)));
    }

    static PointerSlot getTombstoneKey() {
      return PointerSlot(
          reinterpret_cast<const VarDecl *>(static_cast<uintptr_t>(-2)),
          reinterpret_cast<const FieldDecl *>(static_cast<uintptr_t>(-2)));
    }

    static unsigned getHashValue(const PointerSlot &K) {
      return static_cast<unsigned>(llvm::hash_combine(K.VD, K.FD));
    }

    static bool isEqual(const PointerSlot &L, const PointerSlot &R) {
      return L == R;
    }
  };

  using StateMap = llvm::DenseMap<PointerSlot, VarState, PointerSlotDenseMapInfo>;
  using BoolAliasMap = llvm::DenseMap<const VarDecl *, PointerSlot>;

  const BugType BT{this, "", "gjb8114-r-1-3-8"};

  const Expr *stripTransparentExpr(const Expr *E) const {
    while (E) {
      const Expr *Next = E->IgnoreParenImpCasts();
      if (Next != E) {
        E = Next;
        continue;
      }
      if (const auto *CE = dyn_cast<CastExpr>(E)) {
        E = CE->getSubExpr();
        continue;
      }
      break;
    }
    return E;
  }

  PointerSlot getTrackedSlot(const Expr *E) const {
    if (!E)
      return PointerSlot();

    E = stripTransparentExpr(E);

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      const auto *VD = dyn_cast<VarDecl>(DRE->getDecl());
      if (!VD || !VD->getType()->isPointerType())
        return PointerSlot();

      return PointerSlot(VD);
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E)) {
      const auto *FD = dyn_cast<FieldDecl>(ME->getMemberDecl());
      if (!FD || !FD->getType()->isPointerType())
        return PointerSlot();

      const Expr *Base = stripTransparentExpr(ME->getBase());
      if (!Base)
        return PointerSlot();

      if (ME->isArrow()) {
        if (const auto *DRE = dyn_cast<DeclRefExpr>(Base)) {
          const auto *BaseVD = dyn_cast<VarDecl>(DRE->getDecl());
          if (BaseVD)
            return PointerSlot(BaseVD, FD);
        }
        return PointerSlot();
      }

      if (const auto *DRE = dyn_cast<DeclRefExpr>(Base)) {
        const auto *BaseVD = dyn_cast<VarDecl>(DRE->getDecl());
        if (BaseVD)
          return PointerSlot(BaseVD, FD);
      }
    }

    return PointerSlot();
  }

  bool isAllocatorCall(const Expr *E) const {
    E = stripTransparentExpr(E);
    const auto *CE = dyn_cast_or_null<CallExpr>(E);
    if (!CE)
      return false;

    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;

    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  bool isNullConstant(const Expr *E) const {
    E = stripTransparentExpr(E);
    if (!E)
      return false;

    if (isa<CXXNullPtrLiteralExpr>(E) || isa<GNUNullExpr>(E))
      return true;

    if (const auto *IL = dyn_cast<IntegerLiteral>(E))
      return IL->getValue().isZero();

    return false;
  }

  bool resolveCheckedSlot(const Expr *E, const StateMap &States,
                          const BoolAliasMap &Aliases,
                          PointerSlot &Slot) const {
    if (!E)
      return false;

    E = stripTransparentExpr(E);
    if (!E)
      return false;

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_LNot)
        return resolveCheckedSlot(UO->getSubExpr(), States, Aliases, Slot);
      return false;
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      const auto *VD = dyn_cast<VarDecl>(DRE->getDecl());
      if (VD && VD->getType()->isBooleanType()) {
        auto It = Aliases.find(VD);
        if (It != Aliases.end()) {
          Slot = It->second;
          return Slot.isValid() && States.find(Slot) != States.end();
        }
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      const BinaryOperatorKind Op = BO->getOpcode();
      if (Op == BO_EQ || Op == BO_NE) {
        PointerSlot L = getTrackedSlot(BO->getLHS());
        PointerSlot R = getTrackedSlot(BO->getRHS());

        if (L.isValid() && isNullConstant(BO->getRHS())) {
          auto It = States.find(L);
          if (It != States.end()) {
            Slot = L;
            return true;
          }
        }

        if (R.isValid() && isNullConstant(BO->getLHS())) {
          auto It = States.find(R);
          if (It != States.end()) {
            Slot = R;
            return true;
          }
        }
      }
    }

    Slot = getTrackedSlot(E);
    return Slot.isValid() && States.find(Slot) != States.end();
  }

  bool recordBoolAlias(const VarDecl *VD, const Expr *Init, StateMap &States,
                       BoolAliasMap &Aliases) const {
    if (!VD || !VD->getType()->isBooleanType())
      return false;

    PointerSlot Slot;
    if (!resolveCheckedSlot(Init, States, Aliases, Slot))
      return false;

    Aliases[VD] = Slot;
    return true;
  }

  void emitReport(const Expr *Violation, const AnalysisDeclContext *ADC,
                  BugReporter &BR) const {
    SourceLocation Loc = Violation ? Violation->getBeginLoc()
                                   : ADC->getDecl()->getLocation();
    PathDiagnosticLocation PDL(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", PDL);
    if (Violation)
      Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  void markAllocation(PointerSlot Slot, StateMap &States) const {
    if (!Slot.isValid())
      return;

    auto It = States.find(Slot);
    if (It == States.end()) {
      States[Slot] = VarState::Unchecked;
      return;
    }

    if (It->second != VarState::Warned)
      It->second = VarState::Unchecked;
  }

  void markChecked(PointerSlot Slot, StateMap &States) const {
    if (!Slot.isValid())
      return;

    auto It = States.find(Slot);
    if (It == States.end())
      return;

    if (It->second == VarState::Unchecked)
      It->second = VarState::Checked;
  }

  void reportIfNeeded(const Expr *Use, PointerSlot Slot, StateMap &States,
                      const AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!Slot.isValid())
      return;

    auto It = States.find(Slot);
    if (It == States.end() || It->second != VarState::Unchecked)
      return;

    emitReport(Use, ADC, BR);
    It->second = VarState::Warned;
  }

  void processExpr(const Expr *E, StateMap &States, BoolAliasMap &Aliases,
                   const AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!E)
      return;

    E = stripTransparentExpr(E);
    if (!E)
      return;

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      PointerSlot Slot = getTrackedSlot(DRE);
      if (Slot.isValid())
        reportIfNeeded(DRE, Slot, States, ADC, BR);
      return;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E)) {
      PointerSlot Slot = getTrackedSlot(ME);
      if (Slot.isValid()) {
        reportIfNeeded(ME, Slot, States, ADC, BR);
        return;
      }
    }

    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      const FunctionDecl *FD = CE->getDirectCallee();
      if (FD) {
        StringRef Name = FD->getName();
        if (Name == "free" || Name == "realloc")
          return;
      }
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (BO->getOpcode() == BO_Assign) {
        const Expr *RHS = BO->getRHS();

        PointerSlot LHS = getTrackedSlot(BO->getLHS());
        if (LHS.isValid()) {
          processExpr(RHS, States, Aliases, ADC, BR);
          if (isAllocatorCall(RHS))
            markAllocation(LHS, States);
          return;
        }

        if (const auto *LHSDRE =
                dyn_cast<DeclRefExpr>(stripTransparentExpr(BO->getLHS()))) {
          if (const auto *VD = dyn_cast<VarDecl>(LHSDRE->getDecl());
              VD && VD->getType()->isBooleanType()) {
            PointerSlot Slot;
            if (resolveCheckedSlot(RHS, States, Aliases, Slot)) {
              Aliases[VD] = Slot;
              return;
            }
            Aliases.erase(VD);
          }
        }

        processExpr(RHS, States, Aliases, ADC, BR);
        processExpr(BO->getLHS(), States, Aliases, ADC, BR);
        return;
      }
    }

    for (const Stmt *Child : E->children()) {
      if (const auto *ChildExpr = dyn_cast_or_null<Expr>(Child))
        processExpr(ChildExpr, States, Aliases, ADC, BR);
    }
  }

  void processConditionExpr(const Expr *E, StateMap &States,
                            BoolAliasMap &Aliases,
                            const AnalysisDeclContext *ADC,
                            BugReporter &BR) const {
    if (!E)
      return;

    PointerSlot Slot;
    if (resolveCheckedSlot(E, States, Aliases, Slot)) {
      markChecked(Slot, States);
      return;
    }

    processExpr(E, States, Aliases, ADC, BR);
  }

  void processStmt(const Stmt *S, StateMap &States, BoolAliasMap &Aliases,
                   const AnalysisDeclContext *ADC, BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (auto It = CS->body_begin(), End = CS->body_end(); It != End; ++It)
        processStmt(*It, States, Aliases, ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (auto It = DS->decl_begin(), End = DS->decl_end(); It != End; ++It) {
        const auto *VD = dyn_cast<VarDecl>(*It);
        if (!VD)
          continue;

        if (const Expr *Init = VD->getInit()) {
          if (VD->getType()->isBooleanType()) {
            if (recordBoolAlias(VD, Init, States, Aliases))
              continue;
          }

          if (VD->getType()->isPointerType()) {
            processExpr(Init, States, Aliases, ADC, BR);
            if (isAllocatorCall(Init))
              markAllocation(PointerSlot(VD), States);
            continue;
          }

          processExpr(Init, States, Aliases, ADC, BR);
        }
      }
      return;
    }

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      if (const Stmt *Init = IS->getInit())
        processStmt(Init, States, Aliases, ADC, BR);
      processConditionExpr(IS->getCond(), States, Aliases, ADC, BR);
      processStmt(IS->getThen(), States, Aliases, ADC, BR);
      processStmt(IS->getElse(), States, Aliases, ADC, BR);
      return;
    }

    if (const auto *WS = dyn_cast<WhileStmt>(S)) {
      processConditionExpr(WS->getCond(), States, Aliases, ADC, BR);
      processStmt(WS->getBody(), States, Aliases, ADC, BR);
      return;
    }

    if (const auto *FS = dyn_cast<ForStmt>(S)) {
      if (const Stmt *Init = FS->getInit())
        processStmt(Init, States, Aliases, ADC, BR);
      processConditionExpr(FS->getCond(), States, Aliases, ADC, BR);
      processStmt(FS->getBody(), States, Aliases, ADC, BR);
      if (const Expr *Inc = FS->getInc())
        processExpr(Inc, States, Aliases, ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DoStmt>(S)) {
      processStmt(DS->getBody(), States, Aliases, ADC, BR);
      processConditionExpr(DS->getCond(), States, Aliases, ADC, BR);
      return;
    }

    if (const auto *RS = dyn_cast<ReturnStmt>(S)) {
      if (const Expr *Ret = RS->getRetValue())
        processExpr(Ret, States, Aliases, ADC, BR);
      return;
    }

    if (const auto *E = dyn_cast<Expr>(S)) {
      processExpr(E, States, Aliases, ADC, BR);
      return;
    }

    for (const Stmt *Child : S->children())
      processStmt(Child, States, Aliases, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = ADC->getBody();
    if (!Body)
      return;

    StateMap States;
    BoolAliasMap Aliases;
    processStmt(Body, States, Aliases, ADC, BR);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc",
      "Generated checker for unchecked malloc-family pointer use");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;