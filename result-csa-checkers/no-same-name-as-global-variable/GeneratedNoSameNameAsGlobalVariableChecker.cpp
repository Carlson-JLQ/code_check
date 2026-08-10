#include <memory>
#include <string>
#include <unordered_set>

#include "clang/AST/Decl.h"
#include "clang/AST/RecursiveASTVisitor.h"
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

class GeneratedNoSameNameAsGlobalVariableChecker
    : public Checker<check::ASTDecl<TranslationUnitDecl>> {
  const BugType BT{this, "gjb8114-r-1-13-1", "GJB8114"};

  static constexpr const char *DiagnosticText =
      "禁止局部变量与全局变量同名";

  static bool hasIdentifierName(const VarDecl *VD) {
    return VD && VD->getIdentifier();
  }

  static bool isFileOrNamespaceScopeVar(const VarDecl *VD) {
    if (!hasIdentifierName(VD) || isa<ParmVarDecl>(VD))
      return false;

    const DeclContext *DC = VD->getDeclContext();
    return DC && DC->isFileContext();
  }

  static void collectGlobalNamesFromContext(
      const DeclContext *DC, std::unordered_set<std::string> &GlobalNames) {
    if (!DC)
      return;

    for (const Decl *D : DC->decls()) {
      if (const auto *VD = dyn_cast<VarDecl>(D)) {
        if (isFileOrNamespaceScopeVar(VD))
          GlobalNames.insert(VD->getNameAsString());
        continue;
      }

      if (const auto *ND = dyn_cast<NamespaceDecl>(D))
        collectGlobalNamesFromContext(ND, GlobalNames);
    }
  }

  void emitReport(const VarDecl *VD, const Decl *IssueDecl,
                  BugReporter &BR) const {
    PathDiagnosticLocation Location(VD->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report =
        std::make_unique<BasicBugReport>(BT, DiagnosticText, Location);
    Report->addRange(VD->getSourceRange());
    Report->setDeclWithIssue(IssueDecl);
    BR.emitReport(std::move(Report));
  }

  class LocalVariableVisitor
      : public RecursiveASTVisitor<LocalVariableVisitor> {
    const GeneratedNoSameNameAsGlobalVariableChecker &Checker;
    const std::unordered_set<std::string> &GlobalNames;
    BugReporter &BR;
    const Decl *CurrentIssueDecl = nullptr;

  public:
    LocalVariableVisitor(
        const GeneratedNoSameNameAsGlobalVariableChecker &Checker,
        const std::unordered_set<std::string> &GlobalNames,
        BugReporter &BR)
        : Checker(Checker), GlobalNames(GlobalNames), BR(BR) {}

    bool TraverseFunctionDecl(FunctionDecl *FD) {
      if (!FD || !FD->hasBody())
        return true;

      const Decl *PreviousIssueDecl = CurrentIssueDecl;
      CurrentIssueDecl = FD;

      for (const ParmVarDecl *Param : FD->parameters())
        checkLocalVar(Param);

      RecursiveASTVisitor<LocalVariableVisitor>::TraverseStmt(FD->getBody());

      CurrentIssueDecl = PreviousIssueDecl;
      return true;
    }

    bool VisitVarDecl(VarDecl *VD) {
      if (!VD || isa<ParmVarDecl>(VD))
        return true;

      if (isFileOrNamespaceScopeVar(VD))
        return true;

      const DeclContext *DC = VD->getDeclContext();
      if (!DC || DC->isFileContext())
        return true;

      checkLocalVar(VD);
      return true;
    }

  private:
    void checkLocalVar(const VarDecl *VD) {
      if (!hasIdentifierName(VD))
        return;

      if (GlobalNames.find(VD->getNameAsString()) == GlobalNames.end())
        return;

      Checker.emitReport(VD, CurrentIssueDecl ? CurrentIssueDecl : VD, BR);
    }
  };

public:
  void checkASTDecl(const TranslationUnitDecl *TU, AnalysisManager &AM,
                    BugReporter &BR) const {
    (void)AM;

    std::unordered_set<std::string> GlobalNames;
    collectGlobalNamesFromContext(TU, GlobalNames);

    if (GlobalNames.empty())
      return;

    LocalVariableVisitor Visitor(*this, GlobalNames, BR);
    Visitor.TraverseDecl(const_cast<TranslationUnitDecl *>(TU));
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoSameNameAsGlobalVariableChecker>(
      "gjb8114.NoSameNameAsGlobalVariable",
      "Detect local variables with the same name as global variables");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;