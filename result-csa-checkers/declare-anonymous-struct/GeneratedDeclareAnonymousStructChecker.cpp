#include <memory>

#include "clang/AST/Decl.h"
#include "clang/AST/Type.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {
class GeneratedDeclareAnonymousStructChecker
    : public Checker<check::ASTDecl<RecordDecl>> {
  const BugType BT{this, "gjb8114-r-1-1-9", "GJB8114"};

  void report(const FieldDecl *FD, const RecordDecl *Owner, BugReporter &BR) const {
    PathDiagnosticLocation Loc =
        PathDiagnosticLocation::createBegin(FD, BR.getSourceManager());

    auto R = std::make_unique<BasicBugReport>(
        BT, "禁止结构体定义中含有匿名结构体", Loc);
    R->addRange(FD->getSourceRange());
    R->setDeclWithIssue(Owner);
    BR.emitReport(std::move(R));
  }

public:
  void checkASTDecl(const RecordDecl *RD, AnalysisManager &AM,
                    BugReporter &BR) const {
    (void)AM;

    if (!RD || !RD->isThisDeclarationADefinition() || !RD->isStruct())
      return;

    for (const FieldDecl *FD : RD->fields()) {
      if (!FD)
        continue;

      if (!FD->isAnonymousStructOrUnion())
        continue;

      if (FD->getIdentifier())
        continue;

      const RecordType *RT = FD->getType()->getAs<RecordType>();
      if (!RT)
        continue;

      const RecordDecl *Embedded = RT->getDecl();
      if (!Embedded || !(Embedded->isStruct() || Embedded->isUnion()))
        continue;

      report(FD, RD, BR);
    }
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedDeclareAnonymousStructChecker>(
      "gjb8114.DeclareAnonymousStruct",
      "禁止结构体定义中含有匿名结构体");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;