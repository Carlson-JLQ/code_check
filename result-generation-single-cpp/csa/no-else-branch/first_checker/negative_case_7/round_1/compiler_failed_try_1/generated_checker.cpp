#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/Basic/SourceLocation.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  mutable std::unique_ptr<BugType> BT;

  const BugType &getBugType() const {
    if (!BT)
      BT = std::make_unique<BugType>(
          CheckerNameRef("gjb8114.NoElseBranch"),
          "Missing final else branch in if-else if chain");
    return *BT;
  }

  static const IfStmt *getInnermostIf(const IfStmt *If) {
    if (!If)
      return nullptr;

    const IfStmt *Current = If;
    while (const Stmt *Else = Current->getElse()) {
      const auto *NestedIf = dyn_cast<IfStmt>(Else);
      if (!NestedIf)
        break;
      Current = NestedIf;
    }
    return Current;
  }

  static bool hasElseIfChainWithoutFinalElse(const IfStmt *If) {
    if (!If)
      return false;

    const IfStmt *Innermost = getInnermostIf(If);
    return Innermost && If != Innermost && Innermost->getElse() == nullptr;
  }

  static void scanStmt(const Stmt *S, AnalysisManager &AM, BugReporter &BR,
                       const BugType &BT) {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      if (hasElseIfChainWithoutFinalElse(If)) {
        SourceManager &SM = AM.getSourceManager();
        SourceLocation Loc = SM.getSpellingLoc(If->getIfLoc());
        if (Loc.isInvalid())
          Loc = SM.getSpellingLoc(If->getBeginLoc());

        PathDiagnosticLocation PDL = PathDiagnosticLocation::createBegin(
            If, SM, nullptr);

        auto R = std::make_unique<PathSensitiveBugReport>(
            BT, BT.getDescription(), PDL);
        BR.emitReport(std::move(R));
      }

      scanStmt(If->getCond(), AM, BR, BT);
      scanStmt(If->getThen(), AM, BR, BT);
      scanStmt(If->getElse(), AM, BR, BT);
      return;
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, AM, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const BugType &BTRef = getBugType();

    const Stmt *S = nullptr;
    if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D))
      S = FD->getBody();
    else if (const auto *MD = dyn_cast_or_null<ObjCMethodDecl>(D))
      S = MD->getBody();

    if (S)
      scanStmt(S, AM, BR, BTRef);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch",
      "Prohibit omitting the else branch of if-else if statements");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;