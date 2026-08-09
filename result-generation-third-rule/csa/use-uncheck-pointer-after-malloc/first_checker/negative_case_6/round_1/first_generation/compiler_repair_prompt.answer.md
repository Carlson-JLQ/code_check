I’m collapsing this to the compile-time failures first: const-correct source manager access, the invalid `dyn_cast_or_null` branch, and the visitor access specifiers. After that I’ll keep the checker’s public class and registration names intact and make only the smallest changes needed to get it building.I’ve confirmed the current file is trying to do AST traversal with private `Visit*` hooks and one bogus `dyn_cast_or_null<Expr>(nullptr)` path. I’m patching that directly rather than reshaping the checker, because the request is to repair the standalone plugin, not redesign its analysis model.```cpp
#include <memory>
#include <string>
#include <unordered_map>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/RecursiveASTVisitor.h"
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

  struct PtrInfo {
    const VarDecl *VD = nullptr;
    bool Allocated = false;
    bool Checked = false;
    bool Used = false;
    bool Reported = false;
    SourceLocation FirstUseLoc;
  };

  class Visitor : public RecursiveASTVisitor<Visitor> {
    GeneratedUseUncheckPointerAfterMallocChecker &Checker;
    AnalysisDeclContext *ADC;
    BugReporter &BR;
    const SourceManager &SM;
    std::unordered_map<const VarDecl *, PtrInfo> Infos;
    std::unordered_map<std::string, const VarDecl *> GlobalsByName;

    static const Expr *strip(const Expr *E) {
      return E ? E->IgnoreParenImpCasts() : nullptr;
    }

    static const VarDecl *getTargetVar(const Expr *E) {
      E = strip(E);
      if (!E)
        return nullptr;

      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());

      if (const auto *ME = dyn_cast<MemberExpr>(E))
        return dyn_cast<VarDecl>(ME->getMemberDecl());

      return nullptr;
    }

    static const VarDecl *getReferencedVar(const Expr *E) {
      E = strip(E);
      if (!E)
        return nullptr;

      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());

      return nullptr;
    }

    static bool isNullLiteral(const Expr *E) {
      E = strip(E);
      if (!E)
        return false;
      return isa<CXXNullPtrLiteralExpr>(E) || E->isNullPointerConstant(
                                                 *E->getASTContext(),
                                                 Expr::NPC_ValueDependentIsNotNull);
    }

    static bool isAllocCall(const CallExpr *CE) {
      const FunctionDecl *FD = CE ? CE->getDirectCallee() : nullptr;
      if (!FD)
        return false;

      const IdentifierInfo *II = FD->getIdentifier();
      if (!II)
        return false;

      StringRef Name = II->getName();
      return Name == "malloc" || Name == "calloc" || Name == "realloc";
    }

    bool exprUsesTrackedPtr(const Expr *E, const VarDecl *VD) const {
      if (!E)
        return false;

      E = E->IgnoreParenImpCasts();
      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl()) == VD;

      if (const auto *UO = dyn_cast<UnaryOperator>(E))
        return exprUsesTrackedPtr(UO->getSubExpr(), VD);

      for (const Stmt *Child : E->children()) {
        if (const auto *CE = dyn_cast_or_null<Expr>(Child))
          if (exprUsesTrackedPtr(CE, VD))
            return true;
      }
      return false;
    }

    void markChecked(const VarDecl *VD) {
      auto &Info = Infos[VD];
      Info.VD = VD;
      Info.Checked = true;
    }

    void noteUse(const VarDecl *VD, const Expr *UseExpr) {
      auto &Info = Infos[VD];
      Info.VD = VD;
      if (Info.Allocated && !Info.Checked && !Info.Reported) {
        Info.Used = true;
        Info.FirstUseLoc = UseExpr ? UseExpr->getBeginLoc() : SourceLocation();
      }
    }

    void reportIfNeeded(const VarDecl *VD, const Expr *UseExpr) {
      auto &Info = Infos[VD];
      if (!Info.Allocated || Info.Checked || Info.Reported)
        return;

      SourceLocation Loc = UseExpr ? UseExpr->getBeginLoc() : SourceLocation();
      if (Loc.isInvalid())
        Loc = Info.FirstUseLoc.isValid() ? Info.FirstUseLoc : VD->getLocation();

      PathDiagnosticLocation PDL(Loc, SM);
      auto Report = std::make_unique<BasicBugReport>(
          Checker.BT, "禁止动态分配的指针变量未检查即使用", PDL);
      if (UseExpr)
        Report->addRange(UseExpr->getSourceRange());
      Report->addRange(VD->getSourceRange());
      Report->setDeclWithIssue(ADC->getDecl());
      BR.emitReport(std::move(Report));
      Info.Reported = true;
    }

    void scanConditionForCheck(const Expr *Cond) {
      Cond = strip(Cond);
      if (!Cond)
        return;

      if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
        if (UO->getOpcode() == UO_LNot) {
          if (const VarDecl *VD = getReferencedVar(UO->getSubExpr()))
            markChecked(VD);
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
        if (BO->isRelationalOp() || BO->isEqualityOp()) {
          const VarDecl *L = getReferencedVar(BO->getLHS());
          const VarDecl *R = getReferencedVar(BO->getRHS());
          if ((L && isNullLiteral(BO->getRHS())) ||
              (R && isNullLiteral(BO->getLHS())) || L || R) {
            if (L)
              markChecked(L);
            if (R)
              markChecked(R);
          }
        }
      }

      if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond)) {
        if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
          markChecked(VD);
      }
    }

  public:
    Visitor(GeneratedUseUncheckPointerAfterMallocChecker &Checker,
            AnalysisDeclContext *ADC, BugReporter &BR)
        : Checker(Checker), ADC(ADC), BR(BR), SM(BR.getSourceManager()) {}

    bool VisitDeclStmt(DeclStmt *DS) {
      for (Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;

        if (VD->hasGlobalStorage())
          GlobalsByName[VD->getNameAsString()] = VD;

        const Expr *Init = VD->getInit();
        if (const auto *CE = dyn_cast_or_null<CallExpr>(Init)) {
          if (isAllocCall(CE)) {
            auto &Info = Infos[VD];
            Info.VD = VD;
            Info.Allocated = true;
            Info.Checked = false;
            Info.Used = false;
            Info.Reported = false;
          }
        }
      }
      return true;
    }

    bool VisitBinaryOperator(BinaryOperator *BO) {
      if (!BO->isAssignmentOp())
        return true;

      const VarDecl *LHSVar = getTargetVar(BO->getLHS());
      if (!LHSVar)
        return true;

      const Expr *RHS = BO->getRHS();
      if (const auto *CE = dyn_cast_or_null<CallExpr>(strip(RHS))) {
        if (isAllocCall(CE)) {
          auto &Info = Infos[LHSVar];
          Info.VD = LHSVar;
          Info.Allocated = true;
          Info.Checked = false;
          Info.Used = false;
          Info.Reported = false;
          return true;
        }
      }

      if (exprUsesTrackedPtr(RHS, LHSVar)) {
        noteUse(LHSVar, BO);
        reportIfNeeded(LHSVar, BO);
      }
      return true;
    }

    bool VisitIfStmt(IfStmt *IS) {
      scanConditionForCheck(IS->getCond());
      return true;
    }

    bool VisitWhileStmt(WhileStmt *WS) {
      scanConditionForCheck(WS->getCond());
      return true;
    }

    bool VisitDoStmt(DoStmt *DS) {
      scanConditionForCheck(DS->getCond());
      return true;
    }

    bool VisitForStmt(ForStmt *FS) {
      if (FS->getCond())
        scanConditionForCheck(FS->getCond());
      return true;
    }

    bool VisitUnaryOperator(UnaryOperator *UO) {
      if (!(UO->isIncrementDecrementOp() || UO->getOpcode() == UO_Deref))
        return true;

      const VarDecl *VD = getReferencedVar(UO->getSubExpr());
      if (!VD)
        return true;

      auto It = Infos.find(VD);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(VD, UO);
      reportIfNeeded(VD, UO);
      return true;
    }

    bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
      const VarDecl *Base = getReferencedVar(ASE->getBase());
      if (!Base)
        return true;

      auto It = Infos.find(Base);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(Base, ASE);
      reportIfNeeded(Base, ASE);
      return true;
    }

    bool VisitMemberExpr(MemberExpr *ME) {
      const VarDecl *Base = getReferencedVar(ME->getBase());
      if (!Base)
        return true;

      auto It = Infos.find(Base);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(Base, ME);
      reportIfNeeded(Base, ME);
      return true;
    }

    bool VisitCallExpr(CallExpr *CE) {
      if (!CE)
        return true;

      if (isAllocCall(CE))
        return true;

      for (const Expr *Arg : CE->arguments()) {
        const VarDecl *VD = getReferencedVar(Arg);
        if (!VD)
          continue;

        auto It = Infos.find(VD);
        if (It == Infos.end() || !It->second.Allocated)
          continue;

        noteUse(VD, CE);
        reportIfNeeded(VD, CE);
      }
      return true;
    }

    const std::unordered_map<const VarDecl *, PtrInfo> &getInfos() const {
      return Infos;
    }
  };

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(FD);
    if (!ADC)
      return;

    Visitor V(const_cast<GeneratedUseUncheckPointerAfterMallocChecker &>(*this),
              ADC, BR);
    V.TraverseStmt(FD->getBody());
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc",
      "Generated checker for unchecked use of malloc-family pointers");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
```