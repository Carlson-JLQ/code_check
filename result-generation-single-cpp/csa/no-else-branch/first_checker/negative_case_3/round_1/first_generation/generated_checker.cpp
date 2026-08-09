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

  static const IfStmt *getOuterIfChainRoot(const IfStmt *If) {
    const IfStmt *Root = If;
    while (const auto *ParentIf = dyn_cast_or_null<IfStmt>(Root->getParent())) {
      if (ParentIf->getElse() != Root)
        break;
      Root = ParentIf;
    }
    return Root;
  }

  static const IfStmt *getElseIfNodeToReport(const IfStmt *If) {
    const IfStmt *Current = If;
    const IfStmt *LastElseIf = nullptr;

    while (const Stmt *Else = Current->getElse()) {
      const auto *ElseIf = dyn_cast<IfStmt>(Else);
      if (!ElseIf)
        break;
      LastElseIf = ElseIf;
      Current = ElseIf;
    }

    return LastElseIf ? LastElseIf : If;
  }

  void reportMissingElse(const IfStmt *If, BugReporter &BR) const {
    if (!BT)
      BT = std::make_unique<BugType>(this, "No else branch in if-else-if chain",
                                      "gjb8114.NoElseBranch");

    const IfStmt *Anchor = getOuterIfChainRoot(If);
    const IfStmt *ReportNode = getElseIfNodeToReport(Anchor);

    auto R = std::make_unique<PathSensitiveBugReport>(
        *BT, "禁止省略 if-else if 语句的 else 分支", BR.getDataManager().getContext());

    R->setDeclWithIssue(Anchor->getConditionVariableDeclStmt()
                            ? Anchor->getConditionVariableDeclStmt()->getDeclStmt()
                            : nullptr);
    R->setBugLocation(ReportNode->getElse() ? ReportNode->getElse()->getBeginLoc()
                                            : ReportNode->getIfLocStart());
    BR.emitReport(std::move(R));
  }

  static void collectIfChains(const Stmt *S, BugReporter &BR,
                              const GeneratedNoElseBranchChecker &Checker) {
    if (!S)
      return;

    if (const auto *If = dyn_cast<IfStmt>(S)) {
      const Stmt *Else = If->getElse();
      if (Else) {
        if (isa<IfStmt>(Else)) {
          collectIfChains(Else, BR, Checker);
        }
      } else {
        if (If->getElseLoc().isInvalid() || !If->getElseLoc().isValid()) {
          const IfStmt *Root = getOuterIfChainRoot(If);
          if (Root != If || If->getElse() == nullptr) {
            Checker.reportMissingElse(If, BR);
          }
        }
      }
    }

    for (const Stmt *Child : S->children())
      collectIfChains(Child, BR, Checker);
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)D;
    (void)AM;

    if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D)) {
      if (const Stmt *Body = FD->getBody())
        collectIfChains(Body, BR, *this);
      return;
    }

    if (const auto *DC = dyn_cast_or_null<DeclContext>(D)) {
      for (const Decl *Inner : DC->decls()) {
        if (const auto *InnerFD = dyn_cast<FunctionDecl>(Inner)) {
          if (const Stmt *Body = InnerFD->getBody())
            collectIfChains(Body, BR, *this);
        }
      }
    }
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;