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

  static const IfStmt *getMissingElseChainHead(const IfStmt *IfS) {
    const IfStmt *Current = IfS;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return Current;

      const auto *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return nullptr;

      Current = ElseIf;
    }
    return nullptr;
  }

  static void collectIfChains(const Stmt *S,
                              std::vector<const IfStmt *> &Chains) {
    if (!S)
      return;

    if (const auto *IfS = dyn_cast<IfStmt>(S)) {
      if (const IfStmt *Head = getMissingElseChainHead(IfS)) {
        if (!Head->getElse())
          Chains.push_back(Head);
      }

      collectIfChains(IfS->getCond(), Chains);
      collectIfChains(IfS->getThen(), Chains);
      collectIfChains(IfS->getElse(), Chains);
      return;
    }

    for (const Stmt *Child : S->children())
      collectIfChains(Child, Chains);
  }

  void emitReport(const IfStmt *IfS, AnalysisManager &AM, BugReporter &BR) const {
    if (!IfS)
      return;

    if (!BT)
      BT = std::make_unique<BugType>(
          this, "Missing else in if-else if chain", categories::LogicError);

    const auto *AC = AM.getAnalysisDeclContext();
    PathDiagnosticLocation L = AC
                                   ? PathDiagnosticLocation::createBegin(
                                         IfS, AM.getSourceManager(), AC)
                                   : PathDiagnosticLocation::createBegin(
                                         IfS, AM.getSourceManager());

    auto Report = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", L);
    Report->addRange(IfS->getSourceRange());
    BR.emitReport(std::move(Report));
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    if (!D)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<CXXMethodDecl>(D))
      Body = MD->getBody();
    else if (const auto *BD = dyn_cast<BlockDecl>(D))
      Body = BD->getBody();

    if (!Body)
      return;

    std::vector<const IfStmt *> Chains;
    collectIfChains(Body, Chains);

    for (const IfStmt *IfS : Chains)
      emitReport(IfS, AM, BR);
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114.NoElseBranch",
                                                     "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;