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
class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  mutable std::unique_ptr<BugType> BT;

  const BugType &getBugType() const {
    if (!BT)
      BT = std::make_unique<BugType>(
          "No else branch in if-else if chain", "GJB8114");
    return *BT;
  }

  static const IfStmt *getInnermostIf(const IfStmt *IS) {
    const IfStmt *Current = IS;
    while (true) {
      const Stmt *Else = Current->getElse();
      const auto *Nested = dyn_cast_or_null<IfStmt>(Else);
      if (!Nested)
        break;
      Current = Nested;
    }
    return Current;
  }

  static const IfStmt *getTopLevelIfForChain(const IfStmt *IS) {
    const IfStmt *Top = IS;
    const Decl *ParentDecl = nullptr;

    while (const Stmt *Parent = Top->getParentASTContext().getParentMapContext().getParents(*Top).empty()
                                   ? nullptr
                                   : Top->getParentASTContext().getParentMapContext().getParents(*Top)[0].get<Stmt>()) {
      const auto *ParentIf = dyn_cast<IfStmt>(Parent);
      if (!ParentIf)
        break;
      if (ParentIf->getElse() != Top)
        break;
      Top = ParentIf;
    }
    (void)ParentDecl;
    return Top;
  }

  static const IfStmt *findTopLevelIf(const IfStmt *IS) {
    return IS;
  }

  static void collectViolations(const Stmt *S, BugReporter &BR,
                                const BugType &BT) {
    if (!S)
      return;

    for (const Stmt *Child : S->children()) {
      if (const auto *SubIf = dyn_cast_or_null<IfStmt>(Child)) {
        collectViolations(SubIf->getThen(), BR, BT);
        collectViolations(SubIf->getElse(), BR, BT);
        continue;
      }

      if (Child)
        collectViolations(Child, BR, BT);
    }

    const auto *IS = dyn_cast<IfStmt>(S);
    if (!IS)
      return;

    const IfStmt *Top = findTopLevelIf(IS);
    (void)Top;

    bool HasElseIf = false;
    const IfStmt *Current = IS;
    while (Current) {
      const Stmt *Else = Current->getElse();
      const auto *Nested = dyn_cast_or_null<IfStmt>(Else);
      if (!Nested)
        break;
      HasElseIf = true;
      Current = Nested;
    }

    if (!HasElseIf)
      return;

    const IfStmt *Innermost = getInnermostIf(IS);
    if (Innermost->getElse())
      return;

    const Stmt *LocStmt = Innermost->getIfLoc().isValid() ? Innermost->getElse() : nullptr;
    SourceLocation Loc = Innermost->getIfLoc();
    if (Loc.isInvalid())
      return;

    PathDiagnosticLocation DLoc = PathDiagnosticLocation::createBegin(
        Innermost, BR.getSourceManager());
    auto R = std::make_unique<PathSensitiveBugReport>(
        BT, "禁止省略 if-else if 语句的 else 分支", BR.getAnalyzerOptions().getDiagnosticLocation());
    R->setDeclWithIssue(BR.getCurrentDecl());
    R->addRange(SourceRange(Loc, Loc));
    BR.emitReport(std::move(R));
  }

  static void scanStmt(const Stmt *S, BugReporter &BR, const BugType &BT) {
    if (!S)
      return;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      bool HasElseIf = false;
      const IfStmt *Current = IS;
      while (Current) {
        const Stmt *Else = Current->getElse();
        const auto *Nested = dyn_cast_or_null<IfStmt>(Else);
        if (!Nested)
          break;
        HasElseIf = true;
        Current = Nested;
      }

      if (HasElseIf && !Current->getElse()) {
        PathDiagnosticLocation L =
            PathDiagnosticLocation::createBegin(Current->getIfLoc(), BR.getSourceManager());
        if (const Stmt *Then = Current->getThen()) {
          L = PathDiagnosticLocation::createBegin(Then, BR.getSourceManager());
        }
        auto Report = std::make_unique<PathSensitiveBugReport>(
            BT, "禁止省略 if-else if 语句的 else 分支", BR.getAnalyzerOptions().getDiagnosticLocation());
        Report->setDeclWithIssue(BR.getCurrentDecl());
        Report->addRange(Current->getSourceRange());
        BR.emitReport(std::move(Report));
      }

      scanStmt(IS->getCond(), BR, BT);
      scanStmt(IS->getThen(), BR, BT);
      scanStmt(IS->getElse(), BR, BT);
      return;
    }

    for (const Stmt *Child : S->children())
      scanStmt(Child, BR, BT);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    if (!BT)
      BT = std::make_unique<BugType>(
          "No else branch in if-else if chain", "GJB8114");

    scanStmt(FD->getBody(), BR, *BT);
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;