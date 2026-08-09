I’m aligning this with the known ASTCodeBody template and removing the broken path-sensitive machinery. The fix will stay inside the standalone checker source and keep the public class and registration names intact.```cpp
#include <memory>

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

  static bool isAllocationCall(const CallExpr *CE) {
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    IdentifierInfo *II = FD->getIdentifier();
    if (!II)
      return false;
    StringRef Name = II->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static bool isNullConstant(const Expr *E, ASTContext &Ctx) {
    if (!E)
      return false;
    Expr::EvalResult Result;
    if (!E->EvaluateAsInt(Result, Ctx))
      return false;
    return Result.Val.getInt().isZero();
  }

  static const VarDecl *getReferencedVar(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  void scanExpr(const Expr *E, AnalysisDeclContext *ADC, BugReporter &BR,
                llvm::DenseSet<const VarDecl *> &Allocated,
                llvm::DenseSet<const VarDecl *> &Checked,
                llvm::DenseSet<const VarDecl *> &Reported) const {
    if (!E)
      return;

    if (const auto *BO = dyn_cast<BinaryOperator>(E->IgnoreParenImpCasts())) {
      if (BO->isComparisonOp()) {
        const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
        const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
        const VarDecl *VD = getReferencedVar(LHS);
        if (!VD)
          VD = getReferencedVar(RHS);
        if (VD && (isNullConstant(LHS, ADC->getASTContext()) ||
                   isNullConstant(RHS, ADC->getASTContext()))) {
          Checked.insert(VD);
        }
      }
    }

    if (const auto *Call = dyn_cast<CallExpr>(E->IgnoreParenImpCasts())) {
      if (isAllocationCall(Call)) {
        if (const Expr *Arg = Call->getNumArgs() ? Call->getArg(0) : nullptr) {
          if (const VarDecl *VD = getReferencedVar(Arg))
            Allocated.insert(VD);
        }
      }
    }

    if (const VarDecl *VD = getReferencedVar(E)) {
      if (Allocated.count(VD) && !Checked.count(VD) && !Reported.count(VD)) {
        Reported.insert(VD);
        emitASTReport(E, ADC, BR);
      }
    }

    for (const Stmt *Child : E->children()) {
      if (const auto *ChildExpr = dyn_cast_or_null<Expr>(Child))
        scanExpr(ChildExpr, ADC, BR, Allocated, Checked, Reported);
    }
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    llvm::DenseSet<const VarDecl *> Allocated;
    llvm::DenseSet<const VarDecl *> Checked;
    llvm::DenseSet<const VarDecl *> Reported;
    scanExpr(dyn_cast<Expr>(Body), ADC, BR, Allocated, Checked, Reported);
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