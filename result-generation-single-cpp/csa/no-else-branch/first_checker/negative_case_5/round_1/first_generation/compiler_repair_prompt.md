Repair this standalone CSA plugin. Preserve its class and frontend names.
Compiler output:

/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:102:33: error: no template named 'RecursiveASTVisitor'
  102 |   class IfChainVisitor : public RecursiveASTVisitor<IfChainVisitor> {
      |                                 ^
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:47:38: error: no member named 'getParentStmt' in 'clang::IfStmt'
   47 |       const Stmt *ParentElse = Head->getParentStmt();
      |                                ~~~~  ^
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:88:62: error: too few arguments to function call, single argument 'D' was not specified
   88 |                                    AM.getAnalysisDeclContext());
      |                                    ~~~~~~~~~~~~~~~~~~~~~~~~~ ^
/home/llvm/llvm-project/clang/include/clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h:122:24: note: 'getAnalysisDeclContext' declared here
  122 |   AnalysisDeclContext *getAnalysisDeclContext(const Decl *D) {
      |                        ^                      ~~~~~~~~~~~~~
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:87:23: error: no matching constructor for initialization of 'ProgramPoint'
   87 |     ProgramPoint PP = ProgramPoint(ReportStmt, ProgramPoint::PostStmtKind,
      |                       ^            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   88 |                                    AM.getAnalysisDeclContext());
      |                                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/Analysis/ProgramPoint.h:110:3: note: candidate constructor not viable: no known conversion from 'AnalysisDeclContext *' to 'const StackFrame *' for 3rd argument
  110 |   ProgramPoint(const void *P, Kind k, const StackFrame *SF,
      |   ^                                   ~~~~~~~~~~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/Analysis/ProgramPoint.h:60:7: note: candidate constructor (the implicit copy constructor) not viable: requires 1 argument, but 3 were provided
   60 | class ProgramPoint {
      |       ^~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/Analysis/ProgramPoint.h:60:7: note: candidate constructor (the implicit move constructor) not viable: requires 1 argument, but 3 were provided
   60 | class ProgramPoint {
      |       ^~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/Analysis/ProgramPoint.h:109:3: note: candidate constructor not viable: requires 0 arguments, but 3 were provided
  109 |   ProgramPoint() = default;
      |   ^
/home/llvm/llvm-project/clang/include/clang/Analysis/ProgramPoint.h:121:3: note: candidate constructor not viable: requires at least 4 arguments, but 3 were provided
  121 |   ProgramPoint(const void *P1, const void *P2, Kind k, const StackFrame *SF,
      |   ^            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  122 |                const ProgramPointTag *tag = nullptr,
      |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  123 |                CFGBlock::ConstCFGElementRef ElemRef = {nullptr, 0})
      |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:94:71: error: too few arguments to function call, single argument 'D' was not specified
   94 |                                             AM.getAnalysisDeclContext());
      |                                             ~~~~~~~~~~~~~~~~~~~~~~~~~ ^
/home/llvm/llvm-project/clang/include/clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h:122:24: note: 'getAnalysisDeclContext' declared here
  122 |   AnalysisDeclContext *getAnalysisDeclContext(const Decl *D) {
      |                        ^                      ~~~~~~~~~~~~~
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:96:27: error: no member named 'getCurrentAnalysisDeclContext' in 'clang::ento::AnalysisManager'
   96 |     BR.EmitBasicReport(AM.getCurrentAnalysisDeclContext()->getDecl(), this,
      |                        ~~ ^
/home/checker/code_check/result-generation-single-cpp/csa/no-else-branch/first_checker/negative_case_5/round_1/workspace/GeneratedNoElseBranchChecker.cpp:151:13: error: no member named 'TraverseStmt' in '(anonymous namespace)::GeneratedNoElseBranchChecker::IfChainVisitor'
  151 |     Visitor.TraverseStmt(const_cast<Stmt *>(Body));
      |     ~~~~~~~ ^
7 errors generated.

Analysis:
{"repair_steps":["Remove use of `RecursiveASTVisitor` and `TraverseStmt`; this checker should not depend on AST traversal helpers that are not included and are not needed for a body-level checker. Implement the inspection directly with `Stmt` recursion or explicit `dyn_cast<IfStmt>` walking over `Body`.","Replace `IfStmt::getParentStmt()` logic. `IfStmt` does not expose parent pointers in the public API, so chain reconstruction must be done from the enclosing `Stmt` tree while recursing or by tracking the current parent in your own walk.","Stop constructing `ProgramPoint` with `AnalysisManager::getAnalysisDeclContext()`; that API requires a `Decl *` and the `ProgramPoint` constructor signature in this Clang version is different anyway. Prefer emitting reports through `CheckerContext` in a path-sensitive callback, or use only APIs that are actually available in `checkASTCodeBody`.","Replace `AM.getCurrentAnalysisDeclContext()` with the supported source of the declaration, typically the `Decl *D` already passed into `checkASTCodeBody`, or switch the checker to a callback that gives you `CheckerContext` if you need path-sensitive reporting.","Adjust `PathDiagnosticLocation::createBegin` to a signature that matches the available overloads in this Clang version. If you stay in AST-body checking, build the diagnostic location from the statement and `SourceManager` only, or from a `Decl`/`Stmt` pair as supported by the header.","Simplify the implementation to a pure AST checker if the goal is only to detect `if ... else if ...` chains missing a final `else`. In that case, use `checkASTCodeBody` plus recursive `Stmt` inspection and report directly from the enclosing `Decl` rather than mixing AST traversal and analyzer program-point APIs.","Add the missing include only if you keep visitor-based AST traversal, but the cleaner fix is to remove that dependency entirely so the checker compiles against the current CSA headers without extra framework assumptions."],"api_search_terms":["clang::ento::check::ASTCodeBody","clang::ento::CheckerContext::addTransition","clang::ento::CheckerContext::getAnalysisManager","clang::ento::CheckerContext::getState","clang::ento::CheckerContext::getPredecessor","clang::ento::CheckerContext::inTopFrame","clang::ento::CheckerManager::runCheckersForPreStmt","clang::ento::CheckerManager::runCheckersForBranchCondition","clang::ASTVisitor","clang::RecursiveASTVisitor","clang::IfStmt public API getElse getIfLoc getCond","clang::PathDiagnosticLocation::createBegin overloads","clang::ento::AnalysisManager::getAnalysisDeclContext(const Decl *)","clang::ento::ProgramPoint constructors","clang::ento::BugReporter::EmitBasicReport"]}
Relevant APIs:
[{"id": "type:7f7641c5ddc8eab0f238c2c5", "kind": "class", "name": "CheckerContext", "qualified_name": "clang::ento::CheckerContext", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 24, "end_line": 464, "code": "class CheckerContext {\n  ExprEngine &Eng;\n  /// The current exploded(symbolic execution) graph node.\n  ExplodedNode *Pred;\n  /// The flag is true if the (state of the execution) has been modified\n  /// by the checker using this context. For example, a new transition has been\n  /// added or a bug report issued.\n  bool Changed;\n  /// The tagged location, which is used to generate all new nodes.\n  const ProgramPoint Location;\n  NodeBuilder &NB;\n\npublic:\n  /// If we are post visiting a call, this flag will be set if the\n  /// call was inlined.  In all other cases it will be false.\n  const bool wasInlined;\n\n  CheckerContext(NodeBuilder &builder,\n                 ExprEngine &eng,\n                 ExplodedNode *pred,\n                 const ProgramPoint &loc,\n                 bool wasInlined = false)\n    : Eng(eng),\n      Pred(pred),\n      Changed(false),\n      Location(loc),\n      NB(builder),\n      wasInlined(wasInlined) {\n    assert(Pred->getState() &&\n           \"We should not call the checkers on an empty state.\");\n    assert(loc.getTag() && \"The ProgramPoint associated with CheckerContext \"\n                           \"must be tagged with the active checker.\");\n  }\n\n  AnalysisManager &getAnalysisManager() {\n    return Eng.getAnalysisManager();\n  }\n  const AnalysisManager &getAnalysisManager() const {\n    return Eng.getAnalysisManager();\n  }\n\n  ConstraintManager &getConstraintManager() {\n    return Eng.getConstraintManager();\n  }\n  const ConstraintManager &getConstraintManager() const {\n    return Eng.getConstraintManager();\n  }\n\n  StoreManager &getStoreManager() {\n    return Eng.getStoreManager();\n  }\n  const StoreManager &getStoreManager() const { return Eng.getStoreManager(); }\n\n  /// Returns the previous node in the exploded graph, which includes\n  /// the state of the program before the checker ran. Note, checkers should\n  /// not retain the node in their state since the nodes might get invalidated.\n  ExplodedNode *getPredecessor() { return Pred; }\n  const ExplodedNode *getPredecessor() const { return Pred; }\n  const ProgramPoint getLocation() const { return Location; }\n  const ProgramStateRef &getState() const { return Pred->getState(); }\n\n  /// Check if the checker changed the state of the execution; ex: added\n  /// a new transition or a bug report.\n  bool isDifferent() { return Changed; }\n  bool isDifferent() const { return Changed; }\n\n  /// Returns the number of times the current block has been visited\n  /// along the analyzed path.\n  unsigned blockCo"}, "_embedding_id": "type:7f7641c5ddc8eab0f238c2c5", "_similarity": 0.7097353339195251, "_retrieval": "embedding"}, {"id": "api:06f4e46fef82a15eca49be9e", "kind": "method", "name": "inTopFrame", "qualified_name": "clang::ento::CheckerContext::inTopFrame", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "bool inTopFrame() const", "return_type": "bool", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Return true if the current StackFrame has no caller context.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 112, "end_line": 112, "code": "bool inTopFrame() const { return getStackFrame()->inTopFrame(); }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_embedding_id": "api:06f4e46fef82a15eca49be9e", "_similarity": 0.6937334537506104, "_retrieval": "embedding"}, {"id": "api:c1f47706b18503803bcfbf0d", "kind": "method", "name": "runCheckersForBranchCondition", "qualified_name": "clang::ento::CheckerManager::runCheckersForBranchCondition", "namespace": "clang::ento", "owner_id": "type:4e0ae62976b7d5ff24ef2d67", "owner_name": "clang::ento::CheckerManager", "signature": "void runCheckersForBranchCondition(const Stmt *condition, ExplodedNodeSet &Dst, ExplodedNode *Pred, ExprEngine &Eng)", "return_type": "void", "parameters": [{"position": 0, "name": "condition", "type": "const Stmt *", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Dst", "type": "ExplodedNodeSet &", "canonical_type": null, "default_value": null}, {"position": 2, "name": "Pred", "type": "ExplodedNode *", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Eng", "type": "ExprEngine &", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Run checkers for branch condition.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/CheckerManager.h"], "_embedding_id": "api:c1f47706b18503803bcfbf0d", "_similarity": 0.6873645782470703, "_retrieval": "embedding"}, {"id": "type:11c6d57d5e910b03291781a6", "kind": "class", "name": "ConditionTruthVal", "qualified_name": "clang::ento::ConditionTruthVal", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ConstraintManager.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ConstraintManager.h", "start_line": 38, "end_line": 67, "code": "class ConditionTruthVal {\n  std::optional<bool> Val;\n\npublic:\n  /// Construct a ConditionTruthVal indicating the constraint is constrained\n  /// to either true or false, depending on the boolean value provided.\n  ConditionTruthVal(bool constraint) : Val(constraint) {}\n\n  /// Construct a ConstraintVal indicating the constraint is underconstrained.\n  ConditionTruthVal() = default;\n\n  /// \\return Stored value, assuming that the value is known.\n  /// Crashes otherwise.\n  bool getValue() const {\n    return *Val;\n  }\n\n  /// Return true if the constraint is perfectly constrained to 'true'.\n  bool isConstrainedTrue() const { return Val && *Val; }\n\n  /// Return true if the constraint is perfectly constrained to 'false'.\n  bool isConstrainedFalse() const { return Val && !*Val; }\n\n  /// Return true if the constrained is perfectly constrained.\n  bool isConstrained() const { return Val.has_value(); }\n\n  /// Return true if the constrained is underconstrained and we do not know\n  /// if the constraint is true of value.\n  bool isUnderconstrained() const { return !Val.has_value(); }\n}"}, "_embedding_id": "type:11c6d57d5e910b03291781a6", "_similarity": 0.6871547698974609, "_retrieval": "embedding"}, {"id": "api:44dc752e8c7f583827aaefa0", "kind": "method", "name": "isNull", "qualified_name": "clang::ento::ConstraintManager::isNull", "namespace": "clang::ento", "owner_id": "type:b10ac2d0698b20f3411a427d", "owner_name": "clang::ento::ConstraintManager", "signature": "ConditionTruthVal isNull(ProgramStateRef State, SymbolRef Sym)", "return_type": "ConditionTruthVal", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Sym", "type": "SymbolRef", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Convenience method to query the state to see if a symbol is null or\nnot null, or if neither assumption can be made.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ConstraintManager.h", "start_line": 143, "end_line": 145, "code": "ConditionTruthVal isNull(ProgramStateRef State, SymbolRef Sym) {\n    return checkNull(State, Sym);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ConstraintManager.h"], "_embedding_id": "api:44dc752e8c7f583827aaefa0", "_similarity": 0.6857473254203796, "_retrieval": "embedding"}, {"id": "api:0e7fba2949a76c29c97b6336", "kind": "method", "name": "assume", "qualified_name": "clang::ento::ProgramState::assume", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef assume(DefinedOrUnknownSVal cond, bool assumption) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "cond", "type": "DefinedOrUnknownSVal", "canonical_type": null, "default_value": null}, {"position": 1, "name": "assumption", "type": "bool", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "==---------------------------------------------------------------------==//\nConstraints on values.\n==---------------------------------------------------------------------==//\n\nEach ProgramState records constraints on symbolic values.  These constraints\nare managed using the ConstraintManager associated with a ProgramStateManager.\nAs constraints gradually accrue on symbolic values, added constraints\nmay conflict and indicate that a state is infeasible (as no real values\ncould satisfy all the constraints).  This is the principal mechanism\nfor modeling path-sensitivity in ExprEngine/ProgramState.\n\nVarious \"assume\" methods form the interface for adding constraints to\nsymbolic values.  A call to 'assume' indicates an assumption being placed\non one or symbolic values.  'assume' methods take the following inputs:\n\n (1) A ProgramState object representing the current state.\n\n (2) The assumed constraint (which is specific to a given \"assume\" method).\n\n (3) A binary value \"Assumption\" that indicates whether the constraint is\n     assumed to be true or false.\n\nThe output of \"assume*\" is a new ProgramState object with the added constraints.\nIf no new state is feasible, NULL is returned.\n\nAssume", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 702, "end_line": 709, "code": "inline ProgramStateRef ProgramState::assume(DefinedOrUnknownSVal Cond,\n                                      bool Assumption) const {\n  if (Cond.isUnknown())\n    return this;\n\n  return getStateManager().ConstraintMgr\n      ->assume(this, Cond.castAs<DefinedSVal>(), Assumption);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:0e7fba2949a76c29c97b6336", "_similarity": 0.6841477155685425, "_retrieval": "embedding"}, {"id": "api:4c3d514c2b9c3a3f67c491ae", "kind": "method", "name": "runCheckersForPreStmt", "qualified_name": "clang::ento::CheckerManager::runCheckersForPreStmt", "namespace": "clang::ento", "owner_id": "type:4e0ae62976b7d5ff24ef2d67", "owner_name": "clang::ento::CheckerManager", "signature": "void runCheckersForPreStmt(ExplodedNodeSet &Dst, const ExplodedNodeSet &Src, const Stmt *S, ExprEngine &Eng)", "return_type": "void", "parameters": [{"position": 0, "name": "Dst", "type": "ExplodedNodeSet &", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Src", "type": "const ExplodedNodeSet &", "canonical_type": null, "default_value": null}, {"position": 2, "name": "S", "type": "const Stmt *", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Eng", "type": "ExprEngine &", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "===----------------------------------------------------------------------===//\nFunctions for running checkers for path-sensitive checking.\n===----------------------------------------------------------------------===//\nRun checkers for pre-visiting Stmts.\n\nThe notification is performed for every explored CFGElement, which does\nnot include the control flow statements such as IfStmt.\n\n\\sa runCheckersForBranchCondition, runCheckersForPostStmt", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/CheckerManager.h", "start_line": 249, "end_line": 254, "code": "void runCheckersForPreStmt(ExplodedNodeSet &Dst,\n                             const ExplodedNodeSet &Src,\n                             const Stmt *S,\n                             ExprEngine &Eng) {\n    runCheckersForStmt(/*isPreVisit=*/true, Dst, Src, S, Eng);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/CheckerManager.h"], "_embedding_id": "api:4c3d514c2b9c3a3f67c491ae", "_similarity": 0.6840904951095581, "_retrieval": "embedding"}, {"id": "api:e1826157132e6996641cc00a", "kind": "method", "name": "checkNull", "qualified_name": "clang::ento::SMTConstraintManager::checkNull", "namespace": "clang::ento", "owner_id": "type:d13662a1e9f4b7802e7711ee", "owner_name": "clang::ento::SMTConstraintManager", "signature": "ConditionTruthVal checkNull(ProgramStateRef State, SymbolRef Sym) override", "return_type": "ConditionTruthVal", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Sym", "type": "SymbolRef", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": true, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "===------------------------------------------------------------------===//\nImplementation for interface from ConstraintManager.\n===------------------------------------------------------------------===//", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/SMTConstraintManager.h", "start_line": 92, "end_line": 121, "code": "ConditionTruthVal checkNull(ProgramStateRef State, SymbolRef Sym) override {\n    ASTContext &Ctx = getBasicVals().getContext();\n\n    QualType RetTy;\n    // The expression may be casted, so we cannot call getZ3DataExpr() directly\n    std::optional<llvm::SMTExprRef> VarExp =\n        SMTConv::getExpr(Solver, Ctx, Sym, RetTy);\n    if (!VarExp)\n      return ConditionTruthVal();\n    llvm::SMTExprRef Exp = SMTConv::getZeroExpr(Solver, Ctx, VarExp.value(),\n                                                RetTy, /*Assumption=*/true);\n\n    // Negate the constraint\n    llvm::SMTExprRef NotExp = SMTConv::getZeroExpr(Solver, Ctx, VarExp.value(),\n                                                   RetTy, /*Assumption=*/false);\n\n    ConditionTruthVal isSat = checkModel(State, Sym, Exp);\n    ConditionTruthVal isNotSat = checkModel(State, Sym, NotExp);\n\n    // Zero is the only possible solution\n    if (isSat.isConstrainedTrue() && isNotSat.isConstrainedFalse())\n      return true;\n\n    // Zero is not a solution\n    if (isSat.isConstrainedFalse() && isNotSat.isConstrainedTrue())\n      return false;\n\n    // Zero may be a solution\n    return ConditionTruthVal();\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SMTConstraintManager.h"], "_embedding_id": "api:e1826157132e6996641cc00a", "_similarity": 0.6836446523666382, "_retrieval": "embedding"}, {"id": "api:bb5d1fac98d62b06da1c9530", "kind": "method", "name": "addTransition", "qualified_name": "clang::ento::CheckerContext::addTransition", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "ExplodedNode *addTransition(ProgramStateRef State = nullptr, const ProgramPointTag *Tag = nullptr)", "return_type": "ExplodedNode *", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": "nullptr"}, {"position": 1, "name": "Tag", "type": "const ProgramPointTag *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Generates a new transition in the program state graph\n(ExplodedGraph). Uses the default CheckerContext predecessor node.\n\n@param State The state of the generated node. If not specified, the state\n       will not be changed, but the new node will have the checker's tag.\n@param Tag The tag is used to uniquely identify the creation site. If no\n       tag is specified, a default tag, unique to the given checker,\n       will be used. Tags are used to prevent states generated at\n       different sites from caching out.\nNOTE: If the State is unchanged and the Tag is nullptr, this may return a\nnode which is not tagged (instead of using the default tag corresponding\nto the active checker). This is arguably a bug and should be fixed.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 193, "end_line": 196, "code": "ExplodedNode *addTransition(ProgramStateRef State = nullptr,\n                              const ProgramPointTag *Tag = nullptr) {\n    return addTransitionImpl(State ? State : getState(), false, nullptr, Tag);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:d7851a49a76f64c6709a63e9", "kind": "method", "name": "getConstraintManager", "qualified_name": "clang::ento::CheckerContext::getConstraintManager", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "ConstraintManager &getConstraintManager()", "return_type": "ConstraintManager &", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 65, "end_line": 67, "code": "ConstraintManager &getConstraintManager() {\n    return Eng.getConstraintManager();\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:bbdd8c910a6048ce5e673db9", "kind": "method", "name": "getState", "qualified_name": "clang::ento::CheckerContext::getState", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "const ProgramStateRef &getState() const", "return_type": "const ProgramStateRef &", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 83, "end_line": 83, "code": "const ProgramStateRef &getState() const { return Pred->getState(); }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:a93fcaef6e5791ecadd07e91", "kind": "method", "name": "assumeDual", "qualified_name": "clang::ento::ConstraintManager::assumeDual", "namespace": "clang::ento", "owner_id": "type:b10ac2d0698b20f3411a427d", "owner_name": "clang::ento::ConstraintManager", "signature": "ProgramStatePair assumeDual(ProgramStateRef State, DefinedSVal Cond)", "return_type": "ProgramStatePair", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Cond", "type": "DefinedSVal", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns a pair of states (StTrue, StFalse) where the given condition is\nassumed to be true or false, respectively.\n(Note that these two states might be equal if the parent state turns out\nto be infeasible. This may happen if the underlying constraint solver is\nnot perfectly precise and this may happen very rarely.)", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ConstraintManager.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "kind": "method", "name": "get", "qualified_name": "clang::ento::ProgramState::get", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> typename ProgramStateTrait<T>::data_type get() const", "return_type": "typename ProgramStateTrait<T>::data_type", "parameters": [], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 427, "end_line": 431, "code": "template <typename T>\n  typename ProgramStateTrait<T>::data_type\n  get() const {\n    return ProgramStateTrait<T>::MakeData(FindGDM(ProgramStateTrait<T>::GDMIndex()));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:27be6c71f8737ec8709572f6", "kind": "method", "name": "set", "qualified_name": "clang::ento::ProgramState::set", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef set(typename ProgramStateTrait<T>::data_type D) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "D", "type": "typename ProgramStateTrait<T>::data_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 844, "end_line": 847, "code": "template<typename T>\nProgramStateRef ProgramState::set(typename ProgramStateTrait<T>::data_type D) const {\n  return getStateManager().set<T>(this, D);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "type:9dd6ea9e6fc40f462913fff1", "kind": "class", "name": "ASTCodeBody", "qualified_name": "clang::ento::check::ASTCodeBody", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 48, "end_line": 61, "code": "class ASTCodeBody {\n  template <typename CHECKER>\n  static void _checkBody(void *checker, const Decl *D, AnalysisManager& mgr,\n                         BugReporter &BR) {\n    ((const CHECKER *)checker)->checkASTCodeBody(D, mgr, BR);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBody(CheckerManager::CheckDeclFunc(checker,\n                                                       _checkBody<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}, {"id": "type:0cd555dadc4121b45bcf8014", "kind": "class", "name": "BranchCondition", "qualified_name": "clang::ento::check::BranchCondition", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 299, "end_line": 313, "code": "class BranchCondition {\n  template <typename CHECKER>\n  static void _checkBranchCondition(void *checker, const Stmt *Condition,\n                                    CheckerContext & C) {\n    ((const CHECKER *)checker)->checkBranchCondition(Condition, C);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBranchCondition(\n      CheckerManager::CheckBranchConditionFunc(checker,\n                                               _checkBranchCondition<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}]
Relevant MetaOps:
[{"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "state_transition", "meta_op": "Validate a deallocation and mark the released symbol in RegionState.", "behavior": {"preconditions": [], "state_reads": ["RegionState[released symbol]"], "state_writes": ["RegionState[released symbol] = released"], "transitions": [], "reports": []}, "meta_impl": "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr,\n                          const CallEvent &Call, ProgramStateRef State,\n                          bool Hold, bool &IsKnownToBeAllocated,\n                          AllocationFamily Family, bool ReturnsNullOnFailure,\n                          std::optional<SVal> ArgValOpt) const {\n\n  if (!State)\n    return nullptr;\n\n  SVal ArgVal = ArgValOpt.value_or(C.getSVal(ArgExpr));\n  if (!isa<DefinedOrUnknownSVal>(ArgVal))\n    return nullptr;\n  DefinedOrUnknownSVal location = ArgVal.castAs<DefinedOrUnknownSVal>();\n\n  // Check for null dereferences.\n  if (!isa<Loc>(location))\n    return nullptr;\n\n  // The explicit NULL case, no operation is performed.\n  ProgramStateRef notNullState, nullState;\n  std::tie(notNullState, nullState) = State->assume(location);\n  if (nullState && !notNullState)\n    return nullptr;\n\n  // Unknown values could easily be okay\n  // Undefined values are handled elsewhere\n  if (ArgVal.isUnknownOrUndef())\n    return nullptr;\n\n  const MemRegion *R = ArgVal.getAsRegion();\n  const Expr *ParentExpr = Call.getOriginExpr();\n\n  // NOTE: We detected a bug, but the checker under whose name we would emit the\n  // error c", "source_spans": [{"role": "helper", "symbol": "MallocChecker::FreeMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2315, "end_line": 2974}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}], "depends_on": ["metaop:97f65925f14ff701701ae673"], "_embedding_id": "metaop:755cd4eed00d6aa938b1493d", "_similarity": 0.6196844577789307, "_retrieval": "embedding"}, {"checker_id": "checker:7943746b9b88b9f628522043", "implementation_class": "DivZeroChecker", "summary": "DivZeroChecker filters division and remainder operations, constrains the denominator, reports definite zero division, optionally reports tainted-possibly-zero division, and advances analysis on the non-zero path.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:24f41664ae12d8b1e7e5c63e", "name": "DivZero", "registration_function": "ento::registerDivZeroChecker", "frontend_member": "DivideZeroChecker"}, {"id": "frontend:a217bdcbd076008225d3cdd1", "name": "TaintedDiv", "registration_function": "ento::registerTaintedDivChecker", "frontend_member": "TaintedDivChecker"}], "callbacks": ["DivZeroChecker::checkPreStmt"], "kind": "constraint_reasoning", "meta_op": "Split the current program state into zero and non-zero denominator branches using the constraint manager.", "behavior": {"preconditions": ["The denominator is a defined symbolic value."], "state_reads": ["Current program state from the checker context."], "state_writes": ["Derived non-zero and zero successor states."], "transitions": ["Ask the constraint manager to assume the denominator is both non-zero and zero.", "Keep both resulting states for later reporting or continuation."], "reports": []}, "meta_impl": "  // Check for divide by zero.\n  ConstraintManager &CM = C.getConstraintManager();\n  ProgramStateRef stateNotZero, stateZero;\n  std::tie(stateNotZero, stateZero) = CM.assumeDual(C.getState(), *DV);", "source_spans": [{"role": "callback_segment", "symbol": "DivZeroChecker::checkPreStmt", "file": "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp", "start_line": 102, "end_line": 105}], "api_refs": [{"id": "api:46e36ffadcdcb4875da6758a", "qualified_name": "clang::ento::CheckerContext::getConstraintManager"}, {"id": "api:bbdd8c910a6048ce5e673db9", "qualified_name": "clang::ento::CheckerContext::getState"}, {"id": "api:a93fcaef6e5791ecadd07e91", "qualified_name": "clang::ento::ConstraintManager::assumeDual"}], "depends_on": ["metaop:914653be92c745eece103139"], "_embedding_id": "metaop:4b65d6c4013438b35461d664", "_similarity": 0.6196664571762085, "_retrieval": "embedding"}, {"checker_id": "checker:7943746b9b88b9f628522043", "implementation_class": "DivZeroChecker", "summary": "DivZeroChecker filters division and remainder operations, constrains the denominator, reports definite zero division, optionally reports tainted-possibly-zero division, and advances analysis on the non-zero path.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:24f41664ae12d8b1e7e5c63e", "name": "DivZero", "registration_function": "ento::registerDivZeroChecker", "frontend_member": "DivideZeroChecker"}, {"id": "frontend:a217bdcbd076008225d3cdd1", "name": "TaintedDiv", "registration_function": "ento::registerTaintedDivChecker", "frontend_member": "TaintedDivChecker"}], "callbacks": ["DivZeroChecker::checkPreStmt"], "kind": "state_transition", "meta_op": "Advance analysis only along the non-zero denominator branch after any reporting decisions.", "behavior": {"preconditions": ["A non-zero denominator successor state exists."], "state_reads": [], "state_writes": ["Checker exploration continues with the non-zero successor state."], "transitions": ["Abandon the zero-denominator branch.", "Add the non-zero state as the outgoing transition."], "reports": []}, "meta_impl": "  // If we get here, then the denom should not be zero. We abandon the implicit\n  // zero denom case for now.\n  C.addTransition(stateNotZero);\n}", "source_spans": [{"role": "callback_segment", "symbol": "DivZeroChecker::checkPreStmt", "file": "clang/lib/StaticAnalyzer/Checkers/DivZeroChecker.cpp", "start_line": 122, "end_line": 125}], "api_refs": [{"id": "api:2669ca957a0ccf39ad92c422", "qualified_name": "clang::ento::CheckerContext::addTransition"}], "depends_on": ["metaop:4b65d6c4013438b35461d664", "metaop:880edb5f48efae3ad53c5999", "metaop:b62dac122f1fea84e8ea400d"], "_embedding_id": "metaop:b8c055c64848fda17d0f8e5f", "_similarity": 0.6182262301445007, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPostCall", "MallocChecker::checkNewAllocator"], "kind": "state_modeling", "meta_op": "Bind a newly allocated symbol and record its allocation family in RegionState.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": ["RegionState[allocation symbol] = allocated"], "transitions": ["allocation state"], "reports": []}, "meta_impl": "ProgramStateRef MallocChecker::MallocMemAux(CheckerContext &C,\n                                            const CallEvent &Call, SVal Size,\n                                            SVal Init, ProgramStateRef State,\n                                            AllocationFamily Family) const {\n  if (!State)\n    return nullptr;\n\n  const Expr *CE = Call.getOriginExpr();\n\n  // We expect the malloc functions to return a pointer.\n  // Should have been already checked.\n  assert(Loc::isLocType(CE->getType()) &&\n         \"Allocation functions must return a pointer\");\n\n  const StackFrame *SF = C.getPredecessor()->getStackFrame();\n  SVal RetVal = State->getSVal(CE, C.getStackFrame());\n\n  // Fill the region with the initialization value.\n  // FIXME: Why use stack frame of the predecessor?\n  State = State->bindDefaultInitial(RetVal, Init, SF);\n\n  // If Size is somehow undefined at this point, this line prevents a crash.\n  if (Size.isUndef())\n    Size = UnknownVal();\n\n  checkTaintedness(C, Call, Size, State, AllocationFamily(AF_Malloc));\n\n  // Set the region's extent.\n  State = setDynamicExtent(State, RetVal.getAsRegion(),\n                           Size.castAs<DefinedOrUnknownSVal>());\n\n  ret", "source_spans": [{"role": "helper", "symbol": "MallocChecker::MallocMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2060, "end_line": 2140}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}], "depends_on": [], "_embedding_id": "metaop:ab94c1766baa204d15b85804", "_similarity": 0.6079802513122559, "_retrieval": "embedding"}]
Current implementation:
#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

#include <vector>

using namespace clang;
using namespace ento;

namespace {

class GeneratedNoElseBranchChecker : public Checker<check::ASTCodeBody> {
  mutable std::unique_ptr<BugType> BT;

  static const IfStmt *getEnclosingIfStmt(const Stmt *S) {
    if (!S)
      return nullptr;
    return dyn_cast<IfStmt>(S);
  }

  static bool hasElseIfBranch(const IfStmt *IfS) {
    if (!IfS)
      return false;
    const IfStmt *Current = IfS;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return false;
      const IfStmt *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return false;
      Current = ElseIf;
    }
    return true;
  }

  static const IfStmt *getOuterMostChainHead(const IfStmt *IfS) {
    if (!IfS)
      return nullptr;
    const IfStmt *Head = IfS;
    while (true) {
      const Stmt *ParentElse = Head->getParentStmt();
      const IfStmt *ParentIf = dyn_cast_or_null<IfStmt>(ParentElse);
      if (!ParentIf || ParentIf->getElse() != Head)
        break;
      Head = ParentIf;
    }
    return Head;
  }

  static const Stmt *getMissingElseReportLocation(const IfStmt *ChainHead) {
    if (!ChainHead)
      return nullptr;
    const IfStmt *Current = ChainHead;
    while (Current) {
      const Stmt *ElsePart = Current->getElse();
      if (!ElsePart)
        return Current->getIfLoc().getLocWithOffset(0), Current;
      const IfStmt *ElseIf = dyn_cast<IfStmt>(ElsePart);
      if (!ElseIf)
        return nullptr;
      Current = ElseIf;
    }
    return nullptr;
  }

  void reportMissingElse(const IfStmt *ChainHead, AnalysisManager &AM,
                         BugReporter &BR) const {
    if (!ChainHead)
      return;

    if (!BT)
      BT = std::make_unique<BugType>(
          this, "Missing else in if-else if chain",
          categories::LogicError);

    const Stmt *ReportStmt = getMissingElseReportLocation(ChainHead);
    if (!ReportStmt)
      return;

    ExplodedNode *N = nullptr;
    ProgramPoint PP = ProgramPoint(ReportStmt, ProgramPoint::PostStmtKind,
                                   AM.getAnalysisDeclContext());
    (void)PP;

    PathDiagnosticLocation L =
        PathDiagnosticLocation::createBegin(const_cast<Stmt *>(ReportStmt),
                                            AM.getSourceManager(),
                                            AM.getAnalysisDeclContext());

    BR.EmitBasicReport(AM.getCurrentAnalysisDeclContext()->getDecl(), this,
                       "禁止省略 if-else if 语句的 else 分支", "gjb8114-r-1-4-1",
                       "禁止省略 if-else if 语句的 else 分支", L);
    (void)N;
  }

  class IfChainVisitor : public RecursiveASTVisitor<IfChainVisitor> {
    const GeneratedNoElseBranchChecker &Checker;
    AnalysisManager &AM;
    BugReporter &BR;

  public:
    IfChainVisitor(const GeneratedNoElseBranchChecker &Checker,
                   AnalysisManager &AM, BugReporter &BR)
        : Checker(Checker), AM(AM), BR(BR) {}

    bool VisitIfStmt(IfStmt *IfS) {
      if (!IfS)
        return true;

      if (!hasElseIfBranch(IfS))
        return true;

      const IfStmt *Head = getOuterMostChainHead(IfS);
      if (!Head)
        return true;

      const Stmt *ElsePart = Head->getElse();
      if (ElsePart)
        return true;

      Checker.reportMissingElse(Head, AM, BR);
      return true;
    }
  };

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)BR;
    if (!D)
      return;

    const Stmt *Body = nullptr;
    if (const auto *FD = dyn_cast<FunctionDecl>(D))
      Body = FD->getBody();
    else if (const auto *MD = dyn_cast<CXXMethodDecl>(D))
      Body = MD->getBody();
    else if (const auto *OD = dyn_cast<BlockDecl>(D))
      Body = OD->getBody();

    if (!Body)
      return;

    IfChainVisitor Visitor(*this, AM, BR);
    Visitor.TraverseStmt(const_cast<Stmt *>(Body));
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>("gjb8114.NoElseBranch",
                                                     "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
Known compiling implementation template:
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
public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    (void)D;
    (void)AM;
    (void)BR;
    // Implement the retrieved rule logic here.
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedNoElseBranchChecker>(
      "gjb8114.NoElseBranch", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;

When uncertain, restore the template's include set, registration functions,
BugReport construction, and class placement.
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate or include a project-local header.
