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

  static const IfStmt *stripNesting(const Stmt *S) {
    while (S) {
      if (const auto *IS = dyn_cast<IfStmt>(S))
        return IS;
      if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
        if (CS->size() == 1) {
          S = *CS->body_begin();
          continue;
        }
      }
      break;
    }
    return nullptr;
  }

  static const IfStmt *findViolatingIf(const Stmt *S) {
    if (!S)
      return nullptr;

    if (const auto *IS = dyn_cast<IfStmt>(S)) {
      const Stmt *Else = IS->getElse();
      if (!Else) {
        if (const IfStmt *Nested = findViolatingIf(IS->getThen()))
          return Nested;
        return IS;
      }

      if (const IfStmt *Nested = findViolatingIf(IS->getThen()))
        return Nested;
      if (const IfStmt *Nested = findViolatingIf(Else))
        return Nested;

      return nullptr;
    }

    if (const auto *CS = dyn_cast<CompoundStmt>(S)) {
      for (const Stmt *Child : CS->body()) {
        if (const IfStmt *Nested = findViolatingIf(Child))
          return Nested;
      }
      return nullptr;
    }

    for (const Stmt *Child : S->children()) {
      if (const IfStmt *Nested = findViolatingIf(Child))
        return Nested;
    }
    return nullptr;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)AM;

    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD)
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    const IfStmt *ViolatingIf = findViolatingIf(Body);
    if (!ViolatingIf)
      return;

    const IfStmt *ReportedIf = stripNesting(ViolatingIf);
    if (!ReportedIf)
      ReportedIf = ViolatingIf;

    if (!BT)
      BT = std::make_unique<BugType>(
          this, "gjb8114.NoElseBranch", "Static Analyzer Dynamic Checker");

    const SourceManager &SM = BR.getSourceManager();
    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支",
        SM.getLocForEndOfFile(SM.getMainFileID()));

    R->setDeclWithIssue(FD);
    R->setDeclWithIssue(ReportedIf);

    const Stmt *Anchor = ReportedIf->getElse() ? ReportedIf->getElse()
                                               : ReportedIf->getIfLoc().isValid()
                                                     ? ReportedIf
                                                     : Body;
    R->setRange(Anchor->getSourceRange());

    BR.emitReport(std::move(R));
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;