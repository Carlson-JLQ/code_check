I’m checking the local analyzer checker shape first so the plugin matches the existing registration and callback patterns, then I’ll fill in the structural `if / else if` scan and wire the diagnostic to the right token.```cpp
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
          "Missing final else branch in if-else if chain",
          "gjb8114.NoElseBranch");
    return *BT;
  }

  static const IfStmt *getInnermostIf(const IfStmt *If) {
    if (!If)
      return nullptr;

    const IfStmt *Current = If;
    while (true) {
      const Stmt *Else = Current->getElse();
      if (!Else)
        return Current;

      const auto *NestedIf = dyn_cast<IfStmt>(Else->IgnoreImplicit());
      if (!NestedIf)
        return Current;

      Current = NestedIf;
    }
  }

  static SourceLocation getDiagnosticLocation(const IfStmt *If,
                                              SourceManager &SM) {
    const IfStmt *Innermost = getInnermostIf(If);
    if (!Innermost)
      return SourceLocation();

    SourceLocation Loc = Innermost->getIfLoc();
    if (Loc.isInvalid())
      Loc = Innermost->getBeginLoc();

    return SM.getSpellingLoc(Loc);
  }

  static void scanStmt(const Stmt *S, AnalysisManager &AM, BugReporter &BR,
                       const BugType &BT) {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      const IfStmt *Innermost = getInnermostIf(If);
      if (Innermost && Innermost->getElse() == nullptr && If->getElse() != nullptr) {
        PathDiagnosticLocation Loc =
            PathDiagnosticLocation::createBegin(getDiagnosticLocation(Innermost, AM.getSourceManager()),
                                                AM.getSourceManager());
        auto R = std::make_unique<PathSensitiveBugReport>(
            BT.getDescription(), BT, Loc);
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
    const auto *Body = dyn_cast_or_null<Decl>(D);
    (void)Body;
    const BugType &BTRef = getBugType();

    const Stmt *S = nullptr;
    if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D))
      S = FD->getBody();
    else if (const auto *MD = dyn_cast_or_null<ObjCMethodDecl>(D))
      S = MD->getBody();
    else if (const auto *CD = dyn_cast_or_null<CompoundStmt>(D))
      S = CD;

    if (S)
      scanStmt(S, AM, BR, BTRef);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Prohibit omitting the else branch of if-else if statements");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
```