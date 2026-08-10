#include <memory>
#include <vector>

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

using namespace clang;
using namespace ento;

namespace {

class GeneratedRealsePointerNotSetNullChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "gjb8114-r-1-3-6", "GJB8114"};

  struct ReleaseInfo {
    const Stmt *Node = nullptr;
    const VarDecl *Pointer = nullptr;
  };

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止释放指针变量后未置空", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  static const VarDecl *getLocalPointerVar(const Expr *E) {
    if (!E)
      return nullptr;

    E = E->IgnoreParenImpCasts();

    const auto *DRE = dyn_cast<DeclRefExpr>(E);
    if (!DRE)
      return nullptr;

    const auto *VD = dyn_cast<VarDecl>(DRE->getDecl());
    if (!VD)
      return nullptr;

    if (!VD->hasLocalStorage())
      return nullptr;

    if (!VD->getType()->isPointerType())
      return nullptr;

    return VD;
  }

  static bool isFreeCall(const CallExpr *CE) {
    if (!CE || CE->getNumArgs() != 1)
      return false;

    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;

    return FD->getName() == "free";
  }

  static bool isNullPointerValue(const Expr *E, ASTContext &Ctx) {
    if (!E)
      return false;

    E = E->IgnoreParenImpCasts();

    if (isa<CXXNullPtrLiteralExpr>(E))
      return true;

    return E->isNullPointerConstant(Ctx, Expr::NPC_ValueDependentIsNotNull);
  }

  static bool isSamePointerNullAssignment(const Stmt *S, const VarDecl *VD,
                                          ASTContext &Ctx) {
    if (!S || !VD)
      return false;

    const Expr *E = dyn_cast<Expr>(S);
    if (!E)
      return false;

    E = E->IgnoreParenImpCasts();

    const auto *BO = dyn_cast<BinaryOperator>(E);
    if (!BO || !BO->isAssignmentOp())
      return false;

    const VarDecl *LHSVar = getLocalPointerVar(BO->getLHS());
    if (LHSVar != VD)
      return false;

    return isNullPointerValue(BO->getRHS(), Ctx);
  }

  static void collectDirectReleasesInStmt(const Stmt *S,
                                          std::vector<ReleaseInfo> &Releases,
                                          bool IsRoot = true) {
    if (!S)
      return;

    if (!IsRoot && isa<CompoundStmt>(S))
      return;

    if (const auto *CE = dyn_cast<CallExpr>(S)) {
      if (isFreeCall(CE)) {
        if (const VarDecl *VD = getLocalPointerVar(CE->getArg(0)))
          Releases.push_back({CE, VD});
      }
    } else if (const auto *DE = dyn_cast<CXXDeleteExpr>(S)) {
      if (const VarDecl *VD = getLocalPointerVar(DE->getArgument()))
        Releases.push_back({DE, VD});
    }

    for (const Stmt *Child : S->children())
      collectDirectReleasesInStmt(Child, Releases, false);
  }

  void inspectStmt(const Stmt *S, AnalysisDeclContext *ADC, BugReporter &BR,
                   ASTContext &Ctx) const {
    if (!S)
      return;

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (auto It = CS->body_begin(), End = CS->body_end(); It != End; ++It) {
        const Stmt *Current = *It;
        const Stmt *Next = nullptr;

        auto NextIt = It;
        ++NextIt;
        if (NextIt != End)
          Next = *NextIt;

        std::vector<ReleaseInfo> Releases;
        collectDirectReleasesInStmt(Current, Releases);

        for (const ReleaseInfo &Release : Releases) {
          if (!isSamePointerNullAssignment(Next, Release.Pointer, Ctx))
            emitASTReport(Release.Node, ADC, BR);
        }
      }
    }

    for (const Stmt *Child : S->children())
      inspectStmt(Child, ADC, BR, Ctx);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    const Stmt *Body = ADC->getBody();
    if (!Body)
      return;

    inspectStmt(Body, ADC, BR, ADC->getASTContext());
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedRealsePointerNotSetNullChecker>(
      "gjb8114.RealsePointerNotSetNull",
      "Prohibition of failing to set pointers to null after release");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;