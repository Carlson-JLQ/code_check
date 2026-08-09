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
  BugType BT{this, "Missing final else branch in if-else if chain",
             "gjb8114.NoElseBranch"};

  static const IfStmt *unwrapTrailingElseIf(const IfStmt *S) {
    while (S) {
      const Stmt *Else = S->getElse();
      const auto *ElseIf = dyn_cast_or_null<IfStmt>(Else);
      if (!ElseIf)
        break;
      S = ElseIf;
    }
    return S;
  }

  void reportMissingElse(const Decl *D, const Stmt *S, AnalysisManager &AM,
                         BugReporter &BR) const {
    if (!D || !S)
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(D);
    if (!ADC)
      return;

    PathDiagnosticLocation Loc =
        PathDiagnosticLocation::createBegin(S, BR.getSourceManager(), ADC);
    BR.EmitBasicReport(D, this, BT, "Missing else branch", "Control flow",
                       "禁止省略 if-else if 语句的 else 分支", Loc,
                       S->getSourceRange());
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast_or_null<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    llvm::SmallVector<const Stmt *, 64> Worklist;
    Worklist.push_back(Body);

    while (!Worklist.empty()) {
      const Stmt *Cur = Worklist.pop_back_val();
      if (!Cur)
        continue;

      if (const auto *IfS = dyn_cast<IfStmt>(Cur)) {
        const IfStmt *LastIf = unwrapTrailingElseIf(IfS);
        if (IfS->getElse() == nullptr && IfS != LastIf)
          reportMissingElse(D, LastIf, AM, BR);

        if (const Stmt *Then = IfS->getThen())
          Worklist.push_back(Then);
        if (const Stmt *Else = IfS->getElse())
          Worklist.push_back(Else);
        continue;
      }

      for (const Stmt *Child : Cur->children()) {
        if (Child)
          Worklist.push_back(Child);
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