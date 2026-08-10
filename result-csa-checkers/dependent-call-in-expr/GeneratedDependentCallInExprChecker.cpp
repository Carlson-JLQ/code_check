#include <memory>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/DeclCXX.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/Basic/IdentifierTable.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/SmallPtrSet.h"
#include "llvm/ADT/SmallVector.h"

using namespace clang;
using namespace ento;

namespace {

class GeneratedDependentCallInExprChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "gjb8114-r-1-7-14", "GJB8114"};

  enum AccessBits {
    ReadAccess = 1,
    WriteAccess = 2,
  };

  struct AccessSummary {
    llvm::SmallPtrSet<const Decl *, 8> ReadDeps;
    llvm::SmallPtrSet<const Decl *, 8> WriteDeps;
    llvm::SmallPtrSet<const IdentifierInfo *, 4> StaticLocalReadNames;
    llvm::SmallPtrSet<const IdentifierInfo *, 4> StaticLocalWriteNames;
    llvm::DenseMap<const VarDecl *, unsigned> ParamAccess;
  };

  struct CallInfo {
    const CallExpr *Call = nullptr;
    llvm::SmallPtrSet<const Decl *, 8> ReadDeps;
    llvm::SmallPtrSet<const Decl *, 8> WriteDeps;
    llvm::SmallPtrSet<const IdentifierInfo *, 4> StaticLocalReadNames;
    llvm::SmallPtrSet<const IdentifierInfo *, 4> StaticLocalWriteNames;
  };

  void emitASTReport(SourceLocation Loc, SourceRange Range,
                     AnalysisDeclContext *ADC, BugReporter &BR) const {
    PathDiagnosticLocation Location(Loc, BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止同一表达式中调用多个相关函数", Location);
    Report->addRange(Range);
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  static bool isImmutableStorage(const VarDecl *VD) {
    QualType QT = VD->getType();
    return QT.isConstQualified() || VD->isConstexpr();
  }

  static bool isPointerLikeParameter(const ParmVarDecl *PVD) {
    QualType QT = PVD->getType();
    return QT->isPointerType() || QT->isReferenceType() || QT->isArrayType();
  }

  static void addDeclAccess(const VarDecl *VD, unsigned Access,
                            AccessSummary &Summary) {
    if (!VD || !VD->hasGlobalStorage())
      return;

    const bool IsWrite = (Access & WriteAccess) != 0;
    const bool IsRead = (Access & ReadAccess) != 0;

    if (VD->isLocalVarDecl()) {
      if (!IsWrite && isImmutableStorage(VD))
        return;

      if (const IdentifierInfo *II = VD->getIdentifier()) {
        if (IsRead)
          Summary.StaticLocalReadNames.insert(II);
        if (IsWrite)
          Summary.StaticLocalWriteNames.insert(II);
      }
      return;
    }

    const Decl *Canonical = VD->getCanonicalDecl();
    if (IsRead && !isImmutableStorage(VD))
      Summary.ReadDeps.insert(Canonical);
    if (IsWrite)
      Summary.WriteDeps.insert(Canonical);
  }

  static const ParmVarDecl *getReferencedParam(const Expr *E) {
    if (!E)
      return nullptr;

    E = E->IgnoreParenImpCasts();

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      if (const auto *PVD = dyn_cast<ParmVarDecl>(DRE->getDecl()))
        return PVD;
      return nullptr;
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_Deref)
        return getReferencedParam(UO->getSubExpr());
    }

    return nullptr;
  }

  static void addParamPointeeAccess(const ParmVarDecl *PVD, unsigned Access,
                                    AccessSummary &Summary) {
    if (!PVD)
      return;

    if (!isPointerLikeParameter(PVD))
      return;

    const VarDecl *Canonical = PVD->getCanonicalDecl();
    Summary.ParamAccess[Canonical] |= Access;
  }

  static void collectExprAccess(const Expr *E, unsigned Access,
                                AccessSummary &Summary) {
    if (!E)
      return;

    E = E->IgnoreParenImpCasts();

    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (BO->isAssignmentOp()) {
        unsigned LHSAccess = WriteAccess;
        if (BO->isCompoundAssignmentOp())
          LHSAccess |= ReadAccess;

        collectExprAccess(BO->getLHS(), LHSAccess, Summary);
        collectExprAccess(BO->getRHS(), ReadAccess, Summary);
        return;
      }

      collectExprAccess(BO->getLHS(), ReadAccess, Summary);
      collectExprAccess(BO->getRHS(), ReadAccess, Summary);
      return;
    }

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      switch (UO->getOpcode()) {
      case UO_PreInc:
      case UO_PreDec:
      case UO_PostInc:
      case UO_PostDec:
        collectExprAccess(UO->getSubExpr(), ReadAccess | WriteAccess, Summary);
        return;
      case UO_Deref:
        if (const ParmVarDecl *PVD = getReferencedParam(UO->getSubExpr()))
          addParamPointeeAccess(PVD, Access, Summary);
        else
          collectExprAccess(UO->getSubExpr(), ReadAccess, Summary);
        return;
      case UO_AddrOf:
        collectExprAccess(UO->getSubExpr(), ReadAccess, Summary);
        return;
      default:
        collectExprAccess(UO->getSubExpr(), ReadAccess, Summary);
        return;
      }
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E)) {
      const Expr *Base = ME->getBase();
      bool IsPointeeAccess = ME->isArrow();

      if (!IsPointeeAccess) {
        const Expr *IgnoredBase = Base->IgnoreParenImpCasts();
        if (const auto *BaseUO = dyn_cast<UnaryOperator>(IgnoredBase))
          IsPointeeAccess = BaseUO->getOpcode() == UO_Deref;
      }

      if (IsPointeeAccess) {
        if (const ParmVarDecl *PVD = getReferencedParam(Base)) {
          addParamPointeeAccess(PVD, Access, Summary);
          return;
        }
      }

      collectExprAccess(Base, ReadAccess, Summary);
      return;
    }

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E)) {
      if (const ParmVarDecl *PVD = getReferencedParam(ASE->getBase()))
        addParamPointeeAccess(PVD, Access, Summary);
      else
        collectExprAccess(ASE->getBase(), ReadAccess, Summary);

      collectExprAccess(ASE->getIdx(), ReadAccess, Summary);
      return;
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
        addDeclAccess(VD, Access, Summary);
      return;
    }

    if (const auto *CE = dyn_cast<ConditionalOperator>(E)) {
      collectExprAccess(CE->getCond(), ReadAccess, Summary);
      collectExprAccess(CE->getTrueExpr(), Access, Summary);
      collectExprAccess(CE->getFalseExpr(), Access, Summary);
      return;
    }

    for (const Stmt *Child : E->children()) {
      if (const auto *ChildExpr = dyn_cast_or_null<Expr>(Child))
        collectExprAccess(ChildExpr, ReadAccess, Summary);
    }
  }

  static void collectStmtAccess(const Stmt *S, AccessSummary &Summary) {
    if (!S)
      return;

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;

        if (const Expr *Init = VD->getInit())
          collectExprAccess(Init, ReadAccess, Summary);
      }
      return;
    }

    if (const auto *BO = dyn_cast<BinaryOperator>(S)) {
      if (BO->isAssignmentOp()) {
        unsigned LHSAccess = WriteAccess;
        if (BO->isCompoundAssignmentOp())
          LHSAccess |= ReadAccess;

        collectExprAccess(BO->getLHS(), LHSAccess, Summary);
        collectExprAccess(BO->getRHS(), ReadAccess, Summary);
        return;
      }
    }

    if (const auto *E = dyn_cast<Expr>(S)) {
      collectExprAccess(E, ReadAccess, Summary);
      return;
    }

    for (const Stmt *Child : S->children())
      collectStmtAccess(Child, Summary);
  }

  static void addReferencedDecl(const Expr *E,
                                llvm::SmallPtrSetImpl<const Decl *> &Deps) {
    if (!E)
      return;

    E = E->IgnoreParenImpCasts();

    if (const auto *UO = dyn_cast<UnaryOperator>(E)) {
      if (UO->getOpcode() == UO_AddrOf || UO->getOpcode() == UO_Deref) {
        addReferencedDecl(UO->getSubExpr(), Deps);
        return;
      }
    }

    if (const auto *DRE = dyn_cast<DeclRefExpr>(E)) {
      if (const auto *VD = dyn_cast<ValueDecl>(DRE->getDecl()))
        Deps.insert(VD->getCanonicalDecl());
      return;
    }

    if (const auto *ME = dyn_cast<MemberExpr>(E)) {
      addReferencedDecl(ME->getBase(), Deps);
      return;
    }

    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E)) {
      addReferencedDecl(ASE->getBase(), Deps);
      return;
    }

    for (const Stmt *Child : E->children())
      if (const auto *ChildExpr = dyn_cast_or_null<Expr>(Child))
        addReferencedDecl(ChildExpr, Deps);
  }

  static AccessSummary summarizeCallee(const FunctionDecl *FD) {
    AccessSummary Summary;
    if (!FD)
      return Summary;

    if (const Stmt *Body = FD->getBody())
      collectStmtAccess(Body, Summary);

    return Summary;
  }

  static void addCallSiteDepsForArg(const Expr *Arg, unsigned Access,
                                    CallInfo &Info) {
    if (!Arg)
      return;

    if (Access & ReadAccess)
      addReferencedDecl(Arg, Info.ReadDeps);
    if (Access & WriteAccess)
      addReferencedDecl(Arg, Info.WriteDeps);
  }

  static void collectCallInfos(const Stmt *S,
                               llvm::SmallVectorImpl<CallInfo> &Calls) {
    if (!S)
      return;

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      CallInfo Info;
      Info.Call = CE;

      if (const FunctionDecl *FD = CE->getDirectCallee()) {
        AccessSummary Summary = summarizeCallee(FD);

        Info.ReadDeps.insert(Summary.ReadDeps.begin(), Summary.ReadDeps.end());
        Info.WriteDeps.insert(Summary.WriteDeps.begin(), Summary.WriteDeps.end());
        Info.StaticLocalReadNames.insert(Summary.StaticLocalReadNames.begin(),
                                         Summary.StaticLocalReadNames.end());
        Info.StaticLocalWriteNames.insert(Summary.StaticLocalWriteNames.begin(),
                                          Summary.StaticLocalWriteNames.end());

        unsigned ParamCount = FD->getNumParams();
        unsigned ArgCount = CE->getNumArgs();
        unsigned Count = ParamCount < ArgCount ? ParamCount : ArgCount;

        for (unsigned I = 0; I < Count; ++I) {
          const VarDecl *PVD = FD->getParamDecl(I)->getCanonicalDecl();
          auto It = Summary.ParamAccess.find(PVD);
          if (It == Summary.ParamAccess.end())
            continue;

          addCallSiteDepsForArg(CE->getArg(I), It->second, Info);
        }
      }

      Calls.push_back(Info);
    }

    for (const Stmt *Child : S->children())
      collectCallInfos(Child, Calls);
  }

  static bool hasWriteReadConflict(
      const llvm::SmallPtrSetImpl<const Decl *> &LWrites,
      const llvm::SmallPtrSetImpl<const Decl *> &LReads,
      const llvm::SmallPtrSetImpl<const Decl *> &RWrites,
      const llvm::SmallPtrSetImpl<const Decl *> &RReads) {
    for (const Decl *Dep : LWrites) {
      if (RReads.contains(Dep) || RWrites.contains(Dep))
        return true;
    }

    for (const Decl *Dep : RWrites) {
      if (LReads.contains(Dep) || LWrites.contains(Dep))
        return true;
    }

    return false;
  }

  static bool hasStaticNameConflict(
      const llvm::SmallPtrSetImpl<const IdentifierInfo *> &LWrites,
      const llvm::SmallPtrSetImpl<const IdentifierInfo *> &LReads,
      const llvm::SmallPtrSetImpl<const IdentifierInfo *> &RWrites,
      const llvm::SmallPtrSetImpl<const IdentifierInfo *> &RReads) {
    for (const IdentifierInfo *II : LWrites) {
      if (RReads.contains(II) || RWrites.contains(II))
        return true;
    }

    for (const IdentifierInfo *II : RWrites) {
      if (LReads.contains(II) || LWrites.contains(II))
        return true;
    }

    return false;
  }

  static bool shareDependency(const CallInfo &LHS, const CallInfo &RHS) {
    return hasWriteReadConflict(LHS.WriteDeps, LHS.ReadDeps, RHS.WriteDeps,
                                RHS.ReadDeps) ||
           hasStaticNameConflict(LHS.StaticLocalWriteNames,
                                 LHS.StaticLocalReadNames,
                                 RHS.StaticLocalWriteNames,
                                 RHS.StaticLocalReadNames);
  }

  static SourceLocation chooseReportLocation(const Expr *Root,
                                             const CallExpr *SecondCall) {
    if (const auto *BO = dyn_cast<BinaryOperator>(Root->IgnoreParenImpCasts())) {
      if (BO->isAdditiveOp() || BO->isMultiplicativeOp() ||
          BO->isShiftOp() || BO->isBitwiseOp() || BO->isLogicalOp() ||
          BO->isComparisonOp())
        return BO->getOperatorLoc();
    }

    return SecondCall->getBeginLoc();
  }

  void inspectFullExpression(const Expr *E, AnalysisDeclContext *ADC,
                             BugReporter &BR) const {
    if (!E)
      return;

    llvm::SmallVector<CallInfo, 8> Calls;
    collectCallInfos(E, Calls);

    if (Calls.size() < 2)
      return;

    for (unsigned I = 0; I < Calls.size(); ++I) {
      for (unsigned J = I + 1; J < Calls.size(); ++J) {
        if (shareDependency(Calls[I], Calls[J])) {
          emitASTReport(chooseReportLocation(E, Calls[J].Call),
                        E->getSourceRange(), ADC, BR);
          return;
        }
      }
    }
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC,
                   BugReporter &BR) const {
    if (!S)
      return;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body())
        inspectStmt(Child, ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DeclStmt>(S)) {
      for (const Decl *D : DS->decls()) {
        if (const auto *VD = dyn_cast<VarDecl>(D))
          inspectFullExpression(VD->getInit(), ADC, BR);
      }
      return;
    }

    if (const auto *RS = dyn_cast<ReturnStmt>(S)) {
      inspectFullExpression(RS->getRetValue(), ADC, BR);
      return;
    }

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      inspectFullExpression(IS->getCond(), ADC, BR);
      inspectStmt(IS->getThen(), ADC, BR);
      inspectStmt(IS->getElse(), ADC, BR);
      return;
    }

    if (const auto *WS = dyn_cast<WhileStmt>(S)) {
      inspectFullExpression(WS->getCond(), ADC, BR);
      inspectStmt(WS->getBody(), ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DoStmt>(S)) {
      inspectStmt(DS->getBody(), ADC, BR);
      inspectFullExpression(DS->getCond(), ADC, BR);
      return;
    }

    if (const auto *FS = dyn_cast<ForStmt>(S)) {
      inspectStmt(FS->getInit(), ADC, BR);
      inspectFullExpression(FS->getCond(), ADC, BR);
      inspectFullExpression(FS->getInc(), ADC, BR);
      inspectStmt(FS->getBody(), ADC, BR);
      return;
    }

    if (const auto *SS = dyn_cast<SwitchStmt>(S)) {
      inspectFullExpression(SS->getCond(), ADC, BR);
      inspectStmt(SS->getBody(), ADC, BR);
      return;
    }

    if (const auto *LS = dyn_cast<LabelStmt>(S)) {
      inspectStmt(LS->getSubStmt(), ADC, BR);
      return;
    }

    if (const auto *CS = dyn_cast<CaseStmt>(S)) {
      inspectStmt(CS->getSubStmt(), ADC, BR);
      return;
    }

    if (const auto *DS = dyn_cast<DefaultStmt>(S)) {
      inspectStmt(DS->getSubStmt(), ADC, BR);
      return;
    }

    if (const auto *E = dyn_cast<Expr>(S)) {
      inspectFullExpression(E, ADC, BR);
      return;
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, ADC, BR);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    inspectStmt(ADC->getBody(), ADC, BR);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedDependentCallInExprChecker>(
      "gjb8114.DependentCallInExpr", "禁止同一表达式中调用多个相关函数");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;