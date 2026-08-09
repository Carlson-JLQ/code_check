Repair this standalone CSA plugin. Preserve its class and frontend names.
Compiler output:

/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:68:24: error: cannot initialize a parameter of type 'const VarDecl *' with an rvalue of type 'const ValueDecl *'
   68 |         checkExpr(RHS, DRE->getDecl());
      |                        ^~~~~~~~~~~~~~
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:177:50: note: passing argument to parameter 'AssignedVar' here
  177 |     void checkExpr(const Expr *E, const VarDecl *AssignedVar) {
      |                                                  ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:236:15: error: use of undeclared identifier 'isTrackedVarFromExpr'; did you mean 'getTrackedVarFromExpr'?
  236 |       return (isTrackedVarFromExpr(BO->getLHS()) == V &&
      |               ^~~~~~~~~~~~~~~~~~~~
      |               getTrackedVarFromExpr
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:215:25: note: 'getTrackedVarFromExpr' declared here
  215 |   static const VarDecl *getTrackedVarFromExpr(const Expr *E) {
      |                         ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:238:19: error: non-const lvalue reference to type 'ASTContext' cannot bind to a temporary of type 'SourceLocation'
  238 |                   E->getExprLoc(), Expr::NPC_ValueDependentIsNull)) ||
      |                   ^~~~~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/AST/Expr.h:848:19: note: passing argument to parameter 'Ctx' here
  848 |       ASTContext &Ctx,
      |                   ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:239:15: error: use of undeclared identifier 'isTrackedVarFromExpr'; did you mean 'getTrackedVarFromExpr'?
  239 |              (isTrackedVarFromExpr(BO->getRHS()) == V &&
      |               ^~~~~~~~~~~~~~~~~~~~
      |               getTrackedVarFromExpr
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:215:25: note: 'getTrackedVarFromExpr' declared here
  215 |   static const VarDecl *getTrackedVarFromExpr(const Expr *E) {
      |                         ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:241:19: error: non-const lvalue reference to type 'ASTContext' cannot bind to a temporary of type 'SourceLocation'
  241 |                   E->getExprLoc(), Expr::NPC_ValueDependentIsNull));
      |                   ^~~~~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/AST/Expr.h:848:19: note: passing argument to parameter 'Ctx' here
  848 |       ASTContext &Ctx,
      |                   ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_4/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:352:62: error: too few arguments to function call, single argument 'D' was not specified
  352 |               emitASTReport(Later, AM.getAnalysisDeclContext(), BR);
      |                                    ~~~~~~~~~~~~~~~~~~~~~~~~~ ^
/home/llvm/llvm-project/clang/include/clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h:122:24: note: 'getAnalysisDeclContext' declared here
  122 |   AnalysisDeclContext *getAnalysisDeclContext(const Decl *D) {
      |                        ^                      ~~~~~~~~~~~~~
6 errors generated.

Analysis:
{
  "repair_steps": [
    "Fix the type mismatch at `checkExpr(RHS, DRE->getDecl())` by passing a `const VarDecl *`, not a `const ValueDecl *`; use `dyn_cast<VarDecl>(DRE->getDecl())` or change the helper signature only if it is truly meant to accept all value declarations.",
    "Replace the misspelled/undefined `isTrackedVarFromExpr` calls with the existing `getTrackedVarFromExpr` helper, or add a real wrapper with the intended semantics; the current code is calling a function that does not exist.",
    "Correct the `isNullPointerConstant` call at lines 238 and 241: it requires an `ASTContext &` as the first argument, so pass `Ctx` instead of `E->getExprLoc()`.",
    "Fix the `emitASTReport` call to match the actual `AnalysisManager::getAnalysisDeclContext(const Decl *D)` signature by passing the current declaration, for example `AM.getAnalysisDeclContext(D)` instead of calling it with no arguments.",
    "After compilation is restored, sanity-check the checker logic itself: the current implementation mixes AST traversal, allocation detection, and use-order tracking in a way that may produce false positives or miss path-sensitive post-use checks; the likely long-term correction is to model this as a StaticAnalyzer path-sensitive checker using `checkPostCall`, `checkLocation`, and branch-condition handling rather than a plain AST walk.",
    "Add or update a minimal test case that covers malloc/calloc/realloc allocation followed by dereference before null check, plus a case with an immediate null check so the checker still accepts the safe pattern."
  ],
  "api_search_terms": [
    "clang::ento::Checker<check::ASTCodeBody>",
    "clang::ento::AnalysisManager::getAnalysisDeclContext(const Decl *D)",
    "clang::ento::ImplicitNullDerefEvent",
    "clang::ento::CheckerContext::emitReport",
    "clang::ento::ProgramState::invalidateRegions",
    "clang::ento::ProgramState::bindDefaultInitial",
    "clang::ento::ProgramState::get",
    "clang::ento::ProgramState::set",
    "clang::ento::check::BranchCondition",
    "clang::ento::check::ASTCodeBody",
    "MallocChecker::checkPostCall",
    "MallocChecker::checkLocation",
    "MallocChecker::checkPreCall",
    "MallocChecker::MallocMemAux",
    "MallocChecker::FreeMemAux",
    "CallEvent",
    "CallExpr",
    "DeclRefExpr",
    "VarDecl",
    "ValueDecl",
    "ASTContext",
    "SValBuilder::isNullPointerConstant",
    "Expr::isNullPointerConstant"
  ]
}
Original generation context:
{"rule_name": "use-uncheck-pointer-after-malloc", "rule_description": "The rule requires that any pointer obtained through dynamic memory allocation functions (such as malloc, calloc, or realloc) must be checked for non-null before its first use. This check must occur before the pointer is used; performing the check after use is considered a violation. Acceptable check methods include explicit or implicit null pointer comparisons like if (ptr != NULL), if (ptr), or if (!ptr). If a dynamically allocated pointer is never used, it does not violate this rule. If a pointer is reallocated, it must be checked again before any subsequent use. This rule applies equally to global and local variables. Only one warning should be reported per violating pointer variable.\nScenarios that should be reported include: using a dynamically allocated pointer directly without any null check, performing a null check only after the pointer has been used, using a global variable after dynamic allocation without a check, and using pointers from calloc or realloc without a prior check.\nCorrect scenarios include: performing a null check immediately after allocation and using the pointer only after the check passes, not using the pointer after allocation, or not using a pointer after it has been reallocated. Various forms of null pointer checks, including shorthand forms, are acceptable.", "rule_id": "gjb8114-r-1-3-8", "diagnostic": ":[[@LINE]]:9: warning: 禁止动态分配的指针变量未检查即使用", "initial_case": "#include <stdlib.h>\n\nint *p = NULL;\nvoid foo(void)\n{\n    p = (int*) malloc(sizeof(int));\n    *p = 1;\n    // CHECK-MESSAGES: :[[@LINE]]:9: warning: 禁止动态分配的指针变量未检查即使用 [gjb8114-r-1-3-8]\n}", "extracted_logic": [{"intent": "Detect first use of a pointer returned by dynamic allocation without any prior null check.", "trigger": "A value returned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed as a non-null argument, or otherwise used before any null check on that pointer has executed.", "constraints": ["The null check must occur before the first use; a check after first use is a violation.", "Accept explicit and implicit checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.", "If the pointer is never used after allocation, do not report.", "Only one warning should be emitted per violating pointer variable."], "CSA API search terms": ["MallocChecker", "CallEvent", "CallExpr", "VarDecl", "RegionState", "ProgramState", "SVal", "SymbolRef", "checkPostCall", "checkLocation", "checkBind", "assume", "ExprEngine"]}, {"intent": "Detect a null check that happens only after the allocated pointer has already been used.", "trigger": "A pointer from dynamic allocation is used first, and a later conditional null test on the same pointer appears afterward in the control flow.", "constraints": ["Post-use checks do not satisfy the rule.", "The checker must track order of events within a path, not just the presence of a check anywhere in the function.", "Handle both local and global variables."], "CSA API search terms": ["checkPreStmt", "checkPostStmt", "BranchCondition", "BinaryOperator", "UnaryOperator", "ProgramState", "ExplodedNode", "ConstraintManager", "SValBuilder", "assume"]}, {"intent": "Detect use of a global pointer variable after dynamic allocation without a prior null check.", "trigger": "A global variable is assigned the result of `malloc`, `calloc`, or `realloc`, then used before any null check on that same variable.", "constraints": ["Global storage must be tracked the same as local storage.", "A check on another alias or unrelated variable does not satisfy the requirement unless it proves the allocated pointer itself is non-null.", "Report only once per violating variable even if it is used multiple times."], "CSA API search terms": ["GlobalRegion", "VarRegion", "MemRegion", "StoreManager", "ProgramState", "SymbolRef", "LocationContext", "checkBind", "checkLocation", "checkEndFunction"]}, {"intent": "Detect missing re-check after `realloc` before any subsequent use of the returned pointer.", "trigger": "A pointer that has been updated by `realloc` is used before a new null check on that reallocated value.", "constraints": ["Reallocation resets the safety requirement; the pointer must be checked again after `realloc`.", "Do not suppress the warning because the original allocation was checked earlier.", "If the reallocated pointer is never used, do not report.", "Only one warning per pointer variable."], "CSA API search terms": ["ReallocChecker", "MallocChecker", "checkPostCall", "CallEvent", "ProgramState", "SymbolRef", "RegionState", "assume", "checkDeadSymbols"]}, {"intent": "Detect use of pointers from `calloc` or `realloc` without any prior null check.", "trigger": "A pointer returned by `calloc` or `realloc` is used before being tested for null.", "constraints": ["Treat `calloc` and `realloc` the same as `malloc` for this rule.", "Accept shorthand and explicit checks equally.", "A null check after the use is still a violation."], "CSA API search terms": ["CallEvent", "CallExpr", "IdentifierInfo", "FunctionDecl", "MallocChecker", "ProgramState", "SymbolRef", "checkPostCall", "checkLocation"]}, {"intent": "Recognize valid null-check patterns that satisfy the rule before first use.", "trigger": "A pointer from dynamic allocation is guarded by a prior null test such as `if (ptr != NULL)`, `if (ptr)`, or `if (!ptr)` and only then used on the non-null path.", "constraints": ["The checker must understand both explicit comparison and implicit truthiness tests.", "The use must be dominated by the check on the same path.", "If the pointer is not used after the check, do not report."], "CSA API search terms": ["BranchCondition", "BinaryOperator", "UnaryOperator", "Assume", "ProgramState", "ConstraintManager", "ExprEngine", "SValBuilder", "checkBranchCondition"]}], "retrieved_metaops": [{"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkLocation"], "kind": "detection", "meta_op": "Read RegionState on memory access and report use of a released allocation.", "behavior": {"preconditions": [], "state_reads": ["RegionState[accessed symbol]"], "state_writes": [], "transitions": [], "reports": ["Use of memory after it is freed"]}, "meta_impl": "void MallocChecker::checkLocation(SVal l, bool isLoad, const Stmt *S,\n                                  CheckerContext &C) const {\n  SymbolRef Sym = l.getLocSymbolInBase();\n  if (Sym) {\n    checkUseAfterFree(Sym, C, S);\n    checkUseZeroAllocated(Sym, C, S);\n  }\n\nvoid MallocChecker::HandleUseAfterFree(CheckerContext &C, SourceRange Range,\n                                       SymbolRef Sym) const {\n  const UseFree *Frontend = getRelevantFrontendAs<UseFree>(C, Sym);\n  if (!Frontend)\n    return;\n  if (!Frontend->isEnabled()) {\n    C.addSink();\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkLocation", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3668, "end_line": 3674}, {"role": "report_helper", "symbol": "MallocChecker::HandleUseAfterFree", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2798, "end_line": 2806}], "api_refs": [{"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}, {"id": "api:8914c5ed6dc0f00387b69627", "qualified_name": "clang::ento::CheckerContext::emitReport"}], "depends_on": ["metaop:755cd4eed00d6aa938b1493d"], "_embedding_id": "metaop:0c42cf4c9057aa4b060de371", "_similarity": 0.7725169658660889, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "state_transition", "meta_op": "Validate a deallocation and mark the released symbol in RegionState.", "behavior": {"preconditions": [], "state_reads": ["RegionState[released symbol]"], "state_writes": ["RegionState[released symbol] = released"], "transitions": [], "reports": []}, "meta_impl": "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr,\n                          const CallEvent &Call, ProgramStateRef State,\n                          bool Hold, bool &IsKnownToBeAllocated,\n                          AllocationFamily Family, bool ReturnsNullOnFailure,\n                          std::optional<SVal> ArgValOpt) const {\n\n  if (!State)\n    return nullptr;\n\n  SVal ArgVal = ArgValOpt.value_or(C.getSVal(ArgExpr));\n  if (!isa<DefinedOrUnknownSVal>(ArgVal))\n    return nullptr;\n  DefinedOrUnknownSVal location = ArgVal.castAs<DefinedOrUnknownSVal>();\n\n  // Check for null dereferences.\n  if (!isa<Loc>(location))\n    return nullptr;\n\n  // The explicit NULL case, no operation is performed.\n  ProgramStateRef notNullState, nullState;\n  std::tie(notNullState, nullState) = State->assume(location);\n  if (nullState && !notNullState)\n    return nullptr;\n\n  // Unknown values could easily be okay\n  // Undefined values are handled elsewhere\n  if (ArgVal.isUnknownOrUndef())\n    return nullptr;\n\n  const MemRegion *R = ArgVal.getAsRegion();\n  const Expr *ParentExpr = Call.getOriginExpr();\n\n  // NOTE: We detected a bug, but the checker under whose name we would emit the\n  // error c", "source_spans": [{"role": "helper", "symbol": "MallocChecker::FreeMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2315, "end_line": 2974}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}], "depends_on": ["metaop:97f65925f14ff701701ae673"], "_embedding_id": "metaop:755cd4eed00d6aa938b1493d", "_similarity": 0.7714164853096008, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "entry_filter", "meta_op": "Dispatch recognized deallocation and allocation calls to checker-local models.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": [], "transitions": [], "reports": []}, "meta_impl": "void MallocChecker::checkPreCall(const CallEvent &Call,\n                                 CheckerContext &C) const {\n\n  if (const auto *DC = dyn_cast<CXXDeallocatorCall>(&Call)) {\n    const CXXDeleteExpr *DE = DC->getOriginExpr();\n\n    // FIXME: I don't see a good reason for restricting the check against\n    // use-after-free violations to the case when NewDeleteChecker is disabled.\n    // (However, if NewDeleteChecker is enabled, perhaps it would be better to\n    // do this check a bit later?)\n    if (!NewDeleteChecker.isEnabled())\n      if (SymbolRef Sym = C.getSVal(DE->getArgument()).getAsSymbol())\n        checkUseAfterFree(Sym, C, DE->getArgument());\n\n    if (!isStandardNewDelete(DC->getDecl()))\n      return;\n\n    ProgramStateRef State = C.getState();\n    bool IsKnownToBeAllocated;\n    State = FreeMemAux(\n        C, DE->getArgument(), Call, State,\n        /*Hold*/ false, IsKnownToBeAllocated,\n        AllocationFamily(DE->isArrayForm() ? AF_CXXNewArray : AF_CXXNew));\n\n    C.addTransition(State);\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkPreCall", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3445, "end_line": 3471}], "api_refs": [], "depends_on": [], "_embedding_id": "metaop:97f65925f14ff701701ae673", "_similarity": 0.7524878978729248, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPostCall", "MallocChecker::checkNewAllocator"], "kind": "state_modeling", "meta_op": "Bind a newly allocated symbol and record its allocation family in RegionState.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": ["RegionState[allocation symbol] = allocated"], "transitions": ["allocation state"], "reports": []}, "meta_impl": "ProgramStateRef MallocChecker::MallocMemAux(CheckerContext &C,\n                                            const CallEvent &Call, SVal Size,\n                                            SVal Init, ProgramStateRef State,\n                                            AllocationFamily Family) const {\n  if (!State)\n    return nullptr;\n\n  const Expr *CE = Call.getOriginExpr();\n\n  // We expect the malloc functions to return a pointer.\n  // Should have been already checked.\n  assert(Loc::isLocType(CE->getType()) &&\n         \"Allocation functions must return a pointer\");\n\n  const StackFrame *SF = C.getPredecessor()->getStackFrame();\n  SVal RetVal = State->getSVal(CE, C.getStackFrame());\n\n  // Fill the region with the initialization value.\n  // FIXME: Why use stack frame of the predecessor?\n  State = State->bindDefaultInitial(RetVal, Init, SF);\n\n  // If Size is somehow undefined at this point, this line prevents a crash.\n  if (Size.isUndef())\n    Size = UnknownVal();\n\n  checkTaintedness(C, Call, Size, State, AllocationFamily(AF_Malloc));\n\n  // Set the region's extent.\n  State = setDynamicExtent(State, RetVal.getAsRegion(),\n                           Size.castAs<DefinedOrUnknownSVal>());\n\n  ret", "source_spans": [{"role": "helper", "symbol": "MallocChecker::MallocMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2060, "end_line": 2140}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}], "depends_on": [], "_embedding_id": "metaop:ab94c1766baa204d15b85804", "_similarity": 0.7506198287010193, "_retrieval": "embedding"}], "retrieved_api_refs": [{"id": "type:17b2d89e5795205a2881eaf9", "kind": "struct", "name": "ImplicitNullDerefEvent", "qualified_name": "clang::ento::ImplicitNullDerefEvent", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "We dereferenced a location that may be null.", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 624, "end_line": 635, "code": "struct ImplicitNullDerefEvent {\n  SVal Location;\n  bool IsLoad;\n  ExplodedNode *SinkNode;\n  BugReporter *BR;\n  // When true, the dereference is in the source code directly. When false, the\n  // dereference might happen later (for example pointer passed to a parameter\n  // that is marked with nonnull attribute.)\n  bool IsDirectDereference;\n\n  static int Tag;\n}"}, "_embedding_id": "type:17b2d89e5795205a2881eaf9", "_similarity": 0.6966477632522583, "_retrieval": "embedding"}, {"id": "api:5c92afa46cac3694d3ded65e", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::StoreManager::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:d8f2754cb4d89590df1399f1", "owner_name": "clang::ento::StoreManager", "signature": "virtual StoreRef invalidateRegions( Store store, ArrayRef<SVal> Values, ConstCFGElementRef Elem, unsigned Count, const StackFrame *SF, const CallEvent *Call, InvalidatedSymbols &IS, RegionAndSymbolInvalidationTraits &ITraits, InvalidatedRegions *TopLevelRegions, InvalidatedRegions *Invalidated) = 0", "return_type": "StoreRef", "parameters": [{"position": 0, "name": "store", "type": "Store", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Values", "type": "ArrayRef<SVal>", "canonical_type": null, "default_value": null}, {"position": 2, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Count", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 4, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 5, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": null}, {"position": 6, "name": "IS", "type": "InvalidatedSymbols &", "canonical_type": null, "default_value": null}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits &", "canonical_type": null, "default_value": null}, {"position": 8, "name": "TopLevelRegions", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}, {"position": 9, "name": "Invalidated", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": true, "pure_virtual": true, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "invalidateRegions - Clears out the specified regions from the store,\n marking their values as unknown. Depending on the store, this may also\n invalidate additional regions that may have changed based on accessing\n the given regions. If \\p Call is non-null, then this also invalidates\n non-static globals (but if \\p Call is from a system header, then this is\n limited to globals declared in system headers).\n\nInstead of calling this method directly, you should probably use\n\\c ProgramState::invalidateRegions, which calls this and then ensures that\nthe relevant checker callbacks are triggered.\n\n\\param[in] store The initial store.\n\\param[in] Values The values to invalidate.\n\\param[in] Elem The current CFG Element being evaluated. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Count The current block count. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Call The call expression which will be used to determine which\n  globals should get invalidated.\n\\param[in,out] IS A set to fill with any symbols that are no longer\n  accessible. Pass \\c NULL if this information will not be used.\n\\param[in] ITraits Information about invalidati", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/Store.h"], "_embedding_id": "api:5c92afa46cac3694d3ded65e", "_similarity": 0.6898977160453796, "_retrieval": "embedding"}, {"id": "api:b45c2d2855b70b4ff2043dc1", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::ProgramState::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef invalidateRegions( ArrayRef<const MemRegion *> Regions, ConstCFGElementRef Elem, unsigned BlockCount, const StackFrame *SF, bool CausesPointerEscape, InvalidatedSymbols *IS = nullptr, const CallEvent *Call = nullptr, RegionAndSymbolInvalidationTraits *ITraits = nullptr) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "Regions", "type": "ArrayRef<const MemRegion *>", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 2, "name": "BlockCount", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 3, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 4, "name": "CausesPointerEscape", "type": "bool", "canonical_type": null, "default_value": null}, {"position": 5, "name": "IS", "type": "InvalidatedSymbols *", "canonical_type": null, "default_value": "nullptr"}, {"position": 6, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": "nullptr"}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns the state with bindings for the given regions cleared from the\nstore. If \\p Call is non-null, also invalidates global regions (but if\n\\p Call is from a system header, then this is limited to globals declared\nin system headers).\n\nThis calls the lower-level method \\c StoreManager::invalidateRegions to\ndo the actual invalidation, then calls the checker callbacks which should\nbe triggered by this event.\n\n\\param Regions the set of regions to be invalidated.\n\\param Elem The CFG Element that caused the invalidation.\n\\param BlockCount The number of times the current basic block has been\n       visited.\n\\param CausesPointerEscape the flag is set to true when the invalidation\n       entails escape of a symbol (representing a pointer). For example,\n       due to it being passed as an argument in a call.\n\\param IS the set of invalidated symbols.\n\\param Call if non-null, the invalidated regions represent parameters to\n       the call and should be considered directly invalidated.\n\\param ITraits information about special handling for particular regions\n       or symbols.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:b45c2d2855b70b4ff2043dc1", "_similarity": 0.6795912981033325, "_retrieval": "embedding"}, {"id": "api:4162d561535c52fa34f481ba", "kind": "method", "name": "getCapturedRegion", "qualified_name": "clang::ento::BlockDataRegion::getCapturedRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:4162d561535c52fa34f481ba", "_similarity": 0.6777442097663879, "_retrieval": "embedding"}, {"id": "api:75cddbf011a870947e600b61", "kind": "method", "name": "bindDefaultInitial", "qualified_name": "clang::ento::ProgramState::bindDefaultInitial", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef bindDefaultInitial(SVal loc, SVal V, const StackFrame *SF) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "loc", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 1, "name": "V", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 2, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Initializes the region of memory represented by \\p loc with an initial\nvalue. Once initialized, all values loaded from any sub-regions of that\nregion will be equal to \\p V, unless overwritten later by the program.\nThis method should not be used on regions that are already initialized.\nIf you need to indicate that memory contents have suddenly become unknown\nwithin a certain region of memory, consider invalidateRegions().", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:75cddbf011a870947e600b61", "_similarity": 0.6728533506393433, "_retrieval": "embedding"}, {"id": "api:75a14f374e5263695cdb535a", "kind": "method", "name": "getRegion", "qualified_name": "clang::ento::nonloc::LazyCompoundVal::getRegion", "namespace": "clang::ento::nonloc", "owner_id": "type:8d160636bf8e70eabdceae17", "owner_name": "clang::ento::nonloc::LazyCompoundVal", "signature": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *getRegion() const", "return_type": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "This function itself is immaterial. It is only an implementation detail.\nLazyCompoundVal represents only the rvalue, the data (known or unknown)\nthat *was* stored in that region *at some point in the past*. The region\nshould not be used for any purpose other than figuring out what part of\nthe frozen Store you're interested in. The value does not represent the\ncurrent* value of that region. Sometimes it may, but this should not be\nrelied upon. Instead, if you want to figure out what region it represents,\nyou typically need to see where you got it from in the first place. The\nregion is absolutely not analogous to the C++ \"this\" pointer. It is also\nnot a valid way to \"materialize\" the prvalue into a glvalue in C++,\nbecause the region represents the *old* storage (sometimes very old), not\nthe *future* storage.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SVals.h"], "_embedding_id": "api:75a14f374e5263695cdb535a", "_similarity": 0.6718056201934814, "_retrieval": "embedding"}, {"id": "api:07f9154ceaf117fd3a90a68a", "kind": "method", "name": "getOriginalRegion", "qualified_name": "clang::ento::BlockDataRegion::getOriginalRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:07f9154ceaf117fd3a90a68a", "_similarity": 0.6716549396514893, "_retrieval": "embedding"}, {"id": "api:59a9120121473d39ba2a4401", "kind": "method", "name": "getSValAsScalarOrLoc", "qualified_name": "clang::ento::ProgramState::getSValAsScalarOrLoc", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "SVal getSValAsScalarOrLoc(const MemRegion *R) const", "return_type": "SVal", "parameters": [{"position": 0, "name": "R", "type": "const MemRegion *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Return the value bound to the specified location, assuming\nthat the value is a scalar integer or an enumeration or a pointer.\nReturns UnknownVal() if none found or the region is not known to hold\na value of such type.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:59a9120121473d39ba2a4401", "_similarity": 0.6696779727935791, "_retrieval": "embedding"}, {"id": "api:8914c5ed6dc0f00387b69627", "kind": "method", "name": "emitReport", "qualified_name": "clang::ento::CheckerContext::emitReport", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "void emitReport(std::unique_ptr<BugReport> R)", "return_type": "void", "parameters": [{"position": 0, "name": "R", "type": "std::unique_ptr<BugReport>", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Emit the diagnostics report.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 288, "end_line": 291, "code": "void emitReport(std::unique_ptr<BugReport> R) {\n    Changed = true;\n    Eng.getBugReporter().emitReport(std::move(R));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "kind": "method", "name": "get", "qualified_name": "clang::ento::ProgramState::get", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> typename ProgramStateTrait<T>::data_type get() const", "return_type": "typename ProgramStateTrait<T>::data_type", "parameters": [], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 427, "end_line": 431, "code": "template <typename T>\n  typename ProgramStateTrait<T>::data_type\n  get() const {\n    return ProgramStateTrait<T>::MakeData(FindGDM(ProgramStateTrait<T>::GDMIndex()));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:27be6c71f8737ec8709572f6", "kind": "method", "name": "set", "qualified_name": "clang::ento::ProgramState::set", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef set(typename ProgramStateTrait<T>::data_type D) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "D", "type": "typename ProgramStateTrait<T>::data_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 844, "end_line": 847, "code": "template<typename T>\nProgramStateRef ProgramState::set(typename ProgramStateTrait<T>::data_type D) const {\n  return getStateManager().set<T>(this, D);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "type:9dd6ea9e6fc40f462913fff1", "kind": "class", "name": "ASTCodeBody", "qualified_name": "clang::ento::check::ASTCodeBody", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 48, "end_line": 61, "code": "class ASTCodeBody {\n  template <typename CHECKER>\n  static void _checkBody(void *checker, const Decl *D, AnalysisManager& mgr,\n                         BugReporter &BR) {\n    ((const CHECKER *)checker)->checkASTCodeBody(D, mgr, BR);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBody(CheckerManager::CheckDeclFunc(checker,\n                                                       _checkBody<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}, {"id": "type:0cd555dadc4121b45bcf8014", "kind": "class", "name": "BranchCondition", "qualified_name": "clang::ento::check::BranchCondition", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 299, "end_line": 313, "code": "class BranchCondition {\n  template <typename CHECKER>\n  static void _checkBranchCondition(void *checker, const Stmt *Condition,\n                                    CheckerContext & C) {\n    ((const CHECKER *)checker)->checkBranchCondition(Condition, C);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBranchCondition(\n      CheckerManager::CheckBranchConditionFunc(checker,\n                                               _checkBranchCondition<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}]}
Relevant APIs:
[{"id": "type:17b2d89e5795205a2881eaf9", "kind": "struct", "name": "ImplicitNullDerefEvent", "qualified_name": "clang::ento::ImplicitNullDerefEvent", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "We dereferenced a location that may be null.", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 624, "end_line": 635, "code": "struct ImplicitNullDerefEvent {\n  SVal Location;\n  bool IsLoad;\n  ExplodedNode *SinkNode;\n  BugReporter *BR;\n  // When true, the dereference is in the source code directly. When false, the\n  // dereference might happen later (for example pointer passed to a parameter\n  // that is marked with nonnull attribute.)\n  bool IsDirectDereference;\n\n  static int Tag;\n}"}, "_embedding_id": "type:17b2d89e5795205a2881eaf9", "_similarity": 0.6966477632522583, "_retrieval": "embedding"}, {"id": "api:5c92afa46cac3694d3ded65e", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::StoreManager::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:d8f2754cb4d89590df1399f1", "owner_name": "clang::ento::StoreManager", "signature": "virtual StoreRef invalidateRegions( Store store, ArrayRef<SVal> Values, ConstCFGElementRef Elem, unsigned Count, const StackFrame *SF, const CallEvent *Call, InvalidatedSymbols &IS, RegionAndSymbolInvalidationTraits &ITraits, InvalidatedRegions *TopLevelRegions, InvalidatedRegions *Invalidated) = 0", "return_type": "StoreRef", "parameters": [{"position": 0, "name": "store", "type": "Store", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Values", "type": "ArrayRef<SVal>", "canonical_type": null, "default_value": null}, {"position": 2, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Count", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 4, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 5, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": null}, {"position": 6, "name": "IS", "type": "InvalidatedSymbols &", "canonical_type": null, "default_value": null}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits &", "canonical_type": null, "default_value": null}, {"position": 8, "name": "TopLevelRegions", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}, {"position": 9, "name": "Invalidated", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": true, "pure_virtual": true, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "invalidateRegions - Clears out the specified regions from the store,\n marking their values as unknown. Depending on the store, this may also\n invalidate additional regions that may have changed based on accessing\n the given regions. If \\p Call is non-null, then this also invalidates\n non-static globals (but if \\p Call is from a system header, then this is\n limited to globals declared in system headers).\n\nInstead of calling this method directly, you should probably use\n\\c ProgramState::invalidateRegions, which calls this and then ensures that\nthe relevant checker callbacks are triggered.\n\n\\param[in] store The initial store.\n\\param[in] Values The values to invalidate.\n\\param[in] Elem The current CFG Element being evaluated. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Count The current block count. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Call The call expression which will be used to determine which\n  globals should get invalidated.\n\\param[in,out] IS A set to fill with any symbols that are no longer\n  accessible. Pass \\c NULL if this information will not be used.\n\\param[in] ITraits Information about invalidati", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/Store.h"], "_embedding_id": "api:5c92afa46cac3694d3ded65e", "_similarity": 0.6898977160453796, "_retrieval": "embedding"}, {"id": "api:b45c2d2855b70b4ff2043dc1", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::ProgramState::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef invalidateRegions( ArrayRef<const MemRegion *> Regions, ConstCFGElementRef Elem, unsigned BlockCount, const StackFrame *SF, bool CausesPointerEscape, InvalidatedSymbols *IS = nullptr, const CallEvent *Call = nullptr, RegionAndSymbolInvalidationTraits *ITraits = nullptr) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "Regions", "type": "ArrayRef<const MemRegion *>", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 2, "name": "BlockCount", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 3, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 4, "name": "CausesPointerEscape", "type": "bool", "canonical_type": null, "default_value": null}, {"position": 5, "name": "IS", "type": "InvalidatedSymbols *", "canonical_type": null, "default_value": "nullptr"}, {"position": 6, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": "nullptr"}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns the state with bindings for the given regions cleared from the\nstore. If \\p Call is non-null, also invalidates global regions (but if\n\\p Call is from a system header, then this is limited to globals declared\nin system headers).\n\nThis calls the lower-level method \\c StoreManager::invalidateRegions to\ndo the actual invalidation, then calls the checker callbacks which should\nbe triggered by this event.\n\n\\param Regions the set of regions to be invalidated.\n\\param Elem The CFG Element that caused the invalidation.\n\\param BlockCount The number of times the current basic block has been\n       visited.\n\\param CausesPointerEscape the flag is set to true when the invalidation\n       entails escape of a symbol (representing a pointer). For example,\n       due to it being passed as an argument in a call.\n\\param IS the set of invalidated symbols.\n\\param Call if non-null, the invalidated regions represent parameters to\n       the call and should be considered directly invalidated.\n\\param ITraits information about special handling for particular regions\n       or symbols.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:b45c2d2855b70b4ff2043dc1", "_similarity": 0.6795912981033325, "_retrieval": "embedding"}, {"id": "api:4162d561535c52fa34f481ba", "kind": "method", "name": "getCapturedRegion", "qualified_name": "clang::ento::BlockDataRegion::getCapturedRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:4162d561535c52fa34f481ba", "_similarity": 0.6777442097663879, "_retrieval": "embedding"}, {"id": "api:75cddbf011a870947e600b61", "kind": "method", "name": "bindDefaultInitial", "qualified_name": "clang::ento::ProgramState::bindDefaultInitial", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef bindDefaultInitial(SVal loc, SVal V, const StackFrame *SF) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "loc", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 1, "name": "V", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 2, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Initializes the region of memory represented by \\p loc with an initial\nvalue. Once initialized, all values loaded from any sub-regions of that\nregion will be equal to \\p V, unless overwritten later by the program.\nThis method should not be used on regions that are already initialized.\nIf you need to indicate that memory contents have suddenly become unknown\nwithin a certain region of memory, consider invalidateRegions().", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:75cddbf011a870947e600b61", "_similarity": 0.6728533506393433, "_retrieval": "embedding"}, {"id": "api:75a14f374e5263695cdb535a", "kind": "method", "name": "getRegion", "qualified_name": "clang::ento::nonloc::LazyCompoundVal::getRegion", "namespace": "clang::ento::nonloc", "owner_id": "type:8d160636bf8e70eabdceae17", "owner_name": "clang::ento::nonloc::LazyCompoundVal", "signature": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *getRegion() const", "return_type": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "This function itself is immaterial. It is only an implementation detail.\nLazyCompoundVal represents only the rvalue, the data (known or unknown)\nthat *was* stored in that region *at some point in the past*. The region\nshould not be used for any purpose other than figuring out what part of\nthe frozen Store you're interested in. The value does not represent the\ncurrent* value of that region. Sometimes it may, but this should not be\nrelied upon. Instead, if you want to figure out what region it represents,\nyou typically need to see where you got it from in the first place. The\nregion is absolutely not analogous to the C++ \"this\" pointer. It is also\nnot a valid way to \"materialize\" the prvalue into a glvalue in C++,\nbecause the region represents the *old* storage (sometimes very old), not\nthe *future* storage.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SVals.h"], "_embedding_id": "api:75a14f374e5263695cdb535a", "_similarity": 0.6718056201934814, "_retrieval": "embedding"}, {"id": "api:07f9154ceaf117fd3a90a68a", "kind": "method", "name": "getOriginalRegion", "qualified_name": "clang::ento::BlockDataRegion::getOriginalRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:07f9154ceaf117fd3a90a68a", "_similarity": 0.6716549396514893, "_retrieval": "embedding"}, {"id": "api:59a9120121473d39ba2a4401", "kind": "method", "name": "getSValAsScalarOrLoc", "qualified_name": "clang::ento::ProgramState::getSValAsScalarOrLoc", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "SVal getSValAsScalarOrLoc(const MemRegion *R) const", "return_type": "SVal", "parameters": [{"position": 0, "name": "R", "type": "const MemRegion *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Return the value bound to the specified location, assuming\nthat the value is a scalar integer or an enumeration or a pointer.\nReturns UnknownVal() if none found or the region is not known to hold\na value of such type.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:59a9120121473d39ba2a4401", "_similarity": 0.6696779727935791, "_retrieval": "embedding"}, {"id": "api:8914c5ed6dc0f00387b69627", "kind": "method", "name": "emitReport", "qualified_name": "clang::ento::CheckerContext::emitReport", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "void emitReport(std::unique_ptr<BugReport> R)", "return_type": "void", "parameters": [{"position": 0, "name": "R", "type": "std::unique_ptr<BugReport>", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Emit the diagnostics report.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 288, "end_line": 291, "code": "void emitReport(std::unique_ptr<BugReport> R) {\n    Changed = true;\n    Eng.getBugReporter().emitReport(std::move(R));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "kind": "method", "name": "get", "qualified_name": "clang::ento::ProgramState::get", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> typename ProgramStateTrait<T>::data_type get() const", "return_type": "typename ProgramStateTrait<T>::data_type", "parameters": [], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 427, "end_line": 431, "code": "template <typename T>\n  typename ProgramStateTrait<T>::data_type\n  get() const {\n    return ProgramStateTrait<T>::MakeData(FindGDM(ProgramStateTrait<T>::GDMIndex()));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:27be6c71f8737ec8709572f6", "kind": "method", "name": "set", "qualified_name": "clang::ento::ProgramState::set", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef set(typename ProgramStateTrait<T>::data_type D) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "D", "type": "typename ProgramStateTrait<T>::data_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 844, "end_line": 847, "code": "template<typename T>\nProgramStateRef ProgramState::set(typename ProgramStateTrait<T>::data_type D) const {\n  return getStateManager().set<T>(this, D);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "type:9dd6ea9e6fc40f462913fff1", "kind": "class", "name": "ASTCodeBody", "qualified_name": "clang::ento::check::ASTCodeBody", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 48, "end_line": 61, "code": "class ASTCodeBody {\n  template <typename CHECKER>\n  static void _checkBody(void *checker, const Decl *D, AnalysisManager& mgr,\n                         BugReporter &BR) {\n    ((const CHECKER *)checker)->checkASTCodeBody(D, mgr, BR);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBody(CheckerManager::CheckDeclFunc(checker,\n                                                       _checkBody<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}, {"id": "type:0cd555dadc4121b45bcf8014", "kind": "class", "name": "BranchCondition", "qualified_name": "clang::ento::check::BranchCondition", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 299, "end_line": 313, "code": "class BranchCondition {\n  template <typename CHECKER>\n  static void _checkBranchCondition(void *checker, const Stmt *Condition,\n                                    CheckerContext & C) {\n    ((const CHECKER *)checker)->checkBranchCondition(Condition, C);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBranchCondition(\n      CheckerManager::CheckBranchConditionFunc(checker,\n                                               _checkBranchCondition<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}]
Relevant MetaOps:
[{"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkLocation"], "kind": "detection", "meta_op": "Read RegionState on memory access and report use of a released allocation.", "behavior": {"preconditions": [], "state_reads": ["RegionState[accessed symbol]"], "state_writes": [], "transitions": [], "reports": ["Use of memory after it is freed"]}, "meta_impl": "void MallocChecker::checkLocation(SVal l, bool isLoad, const Stmt *S,\n                                  CheckerContext &C) const {\n  SymbolRef Sym = l.getLocSymbolInBase();\n  if (Sym) {\n    checkUseAfterFree(Sym, C, S);\n    checkUseZeroAllocated(Sym, C, S);\n  }\n\nvoid MallocChecker::HandleUseAfterFree(CheckerContext &C, SourceRange Range,\n                                       SymbolRef Sym) const {\n  const UseFree *Frontend = getRelevantFrontendAs<UseFree>(C, Sym);\n  if (!Frontend)\n    return;\n  if (!Frontend->isEnabled()) {\n    C.addSink();\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkLocation", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3668, "end_line": 3674}, {"role": "report_helper", "symbol": "MallocChecker::HandleUseAfterFree", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2798, "end_line": 2806}], "api_refs": [{"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}, {"id": "api:8914c5ed6dc0f00387b69627", "qualified_name": "clang::ento::CheckerContext::emitReport"}], "depends_on": ["metaop:755cd4eed00d6aa938b1493d"], "_embedding_id": "metaop:0c42cf4c9057aa4b060de371", "_similarity": 0.7725169658660889, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "state_transition", "meta_op": "Validate a deallocation and mark the released symbol in RegionState.", "behavior": {"preconditions": [], "state_reads": ["RegionState[released symbol]"], "state_writes": ["RegionState[released symbol] = released"], "transitions": [], "reports": []}, "meta_impl": "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr,\n                          const CallEvent &Call, ProgramStateRef State,\n                          bool Hold, bool &IsKnownToBeAllocated,\n                          AllocationFamily Family, bool ReturnsNullOnFailure,\n                          std::optional<SVal> ArgValOpt) const {\n\n  if (!State)\n    return nullptr;\n\n  SVal ArgVal = ArgValOpt.value_or(C.getSVal(ArgExpr));\n  if (!isa<DefinedOrUnknownSVal>(ArgVal))\n    return nullptr;\n  DefinedOrUnknownSVal location = ArgVal.castAs<DefinedOrUnknownSVal>();\n\n  // Check for null dereferences.\n  if (!isa<Loc>(location))\n    return nullptr;\n\n  // The explicit NULL case, no operation is performed.\n  ProgramStateRef notNullState, nullState;\n  std::tie(notNullState, nullState) = State->assume(location);\n  if (nullState && !notNullState)\n    return nullptr;\n\n  // Unknown values could easily be okay\n  // Undefined values are handled elsewhere\n  if (ArgVal.isUnknownOrUndef())\n    return nullptr;\n\n  const MemRegion *R = ArgVal.getAsRegion();\n  const Expr *ParentExpr = Call.getOriginExpr();\n\n  // NOTE: We detected a bug, but the checker under whose name we would emit the\n  // error c", "source_spans": [{"role": "helper", "symbol": "MallocChecker::FreeMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2315, "end_line": 2974}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}], "depends_on": ["metaop:97f65925f14ff701701ae673"], "_embedding_id": "metaop:755cd4eed00d6aa938b1493d", "_similarity": 0.7714164853096008, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "entry_filter", "meta_op": "Dispatch recognized deallocation and allocation calls to checker-local models.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": [], "transitions": [], "reports": []}, "meta_impl": "void MallocChecker::checkPreCall(const CallEvent &Call,\n                                 CheckerContext &C) const {\n\n  if (const auto *DC = dyn_cast<CXXDeallocatorCall>(&Call)) {\n    const CXXDeleteExpr *DE = DC->getOriginExpr();\n\n    // FIXME: I don't see a good reason for restricting the check against\n    // use-after-free violations to the case when NewDeleteChecker is disabled.\n    // (However, if NewDeleteChecker is enabled, perhaps it would be better to\n    // do this check a bit later?)\n    if (!NewDeleteChecker.isEnabled())\n      if (SymbolRef Sym = C.getSVal(DE->getArgument()).getAsSymbol())\n        checkUseAfterFree(Sym, C, DE->getArgument());\n\n    if (!isStandardNewDelete(DC->getDecl()))\n      return;\n\n    ProgramStateRef State = C.getState();\n    bool IsKnownToBeAllocated;\n    State = FreeMemAux(\n        C, DE->getArgument(), Call, State,\n        /*Hold*/ false, IsKnownToBeAllocated,\n        AllocationFamily(DE->isArrayForm() ? AF_CXXNewArray : AF_CXXNew));\n\n    C.addTransition(State);\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkPreCall", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3445, "end_line": 3471}], "api_refs": [], "depends_on": [], "_embedding_id": "metaop:97f65925f14ff701701ae673", "_similarity": 0.7524878978729248, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPostCall", "MallocChecker::checkNewAllocator"], "kind": "state_modeling", "meta_op": "Bind a newly allocated symbol and record its allocation family in RegionState.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": ["RegionState[allocation symbol] = allocated"], "transitions": ["allocation state"], "reports": []}, "meta_impl": "ProgramStateRef MallocChecker::MallocMemAux(CheckerContext &C,\n                                            const CallEvent &Call, SVal Size,\n                                            SVal Init, ProgramStateRef State,\n                                            AllocationFamily Family) const {\n  if (!State)\n    return nullptr;\n\n  const Expr *CE = Call.getOriginExpr();\n\n  // We expect the malloc functions to return a pointer.\n  // Should have been already checked.\n  assert(Loc::isLocType(CE->getType()) &&\n         \"Allocation functions must return a pointer\");\n\n  const StackFrame *SF = C.getPredecessor()->getStackFrame();\n  SVal RetVal = State->getSVal(CE, C.getStackFrame());\n\n  // Fill the region with the initialization value.\n  // FIXME: Why use stack frame of the predecessor?\n  State = State->bindDefaultInitial(RetVal, Init, SF);\n\n  // If Size is somehow undefined at this point, this line prevents a crash.\n  if (Size.isUndef())\n    Size = UnknownVal();\n\n  checkTaintedness(C, Call, Size, State, AllocationFamily(AF_Malloc));\n\n  // Set the region's extent.\n  State = setDynamicExtent(State, RetVal.getAsRegion(),\n                           Size.castAs<DefinedOrUnknownSVal>());\n\n  ret", "source_spans": [{"role": "helper", "symbol": "MallocChecker::MallocMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2060, "end_line": 2140}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}], "depends_on": [], "_embedding_id": "metaop:ab94c1766baa204d15b85804", "_similarity": 0.7506198287010193, "_retrieval": "embedding"}]
Current implementation:
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Expr.h"
#include "clang/AST/RecursiveASTVisitor.h"
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

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  class BodyVisitor : public RecursiveASTVisitor<BodyVisitor> {
  public:
    struct UseSite {
      const DeclRefExpr *Ref = nullptr;
      const Expr *ExprNode = nullptr;
      const VarDecl *Var = nullptr;
      unsigned Order = 0;
    };

    explicit BodyVisitor(ASTContext &Ctx) : Ctx(Ctx) {}

    void setDecl(const Decl *D) {
      RootDecl = D;
      if (const auto *FD = dyn_cast_or_null<FunctionDecl>(D))
        RootBody = FD->getBody();
      else if (const auto *VD = dyn_cast_or_null<VarDecl>(D))
        if (const Expr *Init = VD->getInit())
          RootBody = Init;
    }

    const std::vector<UseSite> &getUses() const { return Uses; }

    bool VisitDeclStmt(DeclStmt *DS) {
      for (DeclStmt::decl_iterator I = DS->decl_begin(), E = DS->decl_end();
           I != E; ++I) {
        if (const auto *VD = dyn_cast<VarDecl>(*I)) {
          if (const Expr *Init = VD->getInit())
            checkExpr(Init, VD);
        }
      }
      return true;
    }

    bool VisitBinaryOperator(BinaryOperator *BO) {
      if (!BO->isAssignmentOp())
        return true;
      const Expr *LHS = BO->getLHS()->IgnoreParenImpCasts();
      const Expr *RHS = BO->getRHS()->IgnoreParenImpCasts();
      if (const auto *DRE = dyn_cast<DeclRefExpr>(LHS))
        checkExpr(RHS, DRE->getDecl());
      return true;
    }

    bool VisitReturnStmt(ReturnStmt *RS) {
      if (const Expr *Ret = RS->getRetValue())
        checkExpr(Ret, nullptr);
      return true;
    }

    bool VisitUnaryOperator(UnaryOperator *UO) {
      if (UO->getOpcode() == UO_Deref)
        noteUse(UO->getSubExpr()->IgnoreParenImpCasts(), UO);
      return true;
    }

    bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
      noteUse(ASE->getBase()->IgnoreParenImpCasts(), ASE);
      noteUse(ASE->getIdx()->IgnoreParenImpCasts(), ASE);
      return true;
    }

    bool VisitMemberExpr(MemberExpr *ME) {
      noteUse(ME->getBase()->IgnoreParenImpCasts(), ME);
      return true;
    }

    bool VisitCallExpr(CallExpr *CE) {
      for (const Expr *Arg : CE->arguments())
        noteUse(Arg->IgnoreParenImpCasts(), CE);
      return true;
    }

    bool VisitIfStmt(IfStmt *IS) {
      if (const Expr *Cond = IS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitWhileStmt(WhileStmt *WS) {
      if (const Expr *Cond = WS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitForStmt(ForStmt *FS) {
      if (const Expr *Cond = FS->getCond())
        checkCondition(Cond->IgnoreParenImpCasts());
      return true;
    }

    bool VisitConditionalOperator(ConditionalOperator *CO) {
      checkCondition(CO->getCond()->IgnoreParenImpCasts());
      return true;
    }

  private:
    ASTContext &Ctx;
    const Decl *RootDecl = nullptr;
    const Stmt *RootBody = nullptr;
    std::vector<UseSite> Uses;
    unsigned NextOrder = 0;
    std::set<const VarDecl *> CheckedVars;

    static bool isMallocLikeName(StringRef Name) {
      return Name == "malloc" || Name == "calloc" || Name == "realloc";
    }

    bool isAllocationCall(const Expr *E) const {
      const auto *CE = dyn_cast_or_null<CallExpr>(E->IgnoreParenImpCasts());
      if (!CE)
        return false;
      const FunctionDecl *FD = CE->getDirectCallee();
      if (!FD)
        return false;
      return isMallocLikeName(FD->getName());
    }

    const VarDecl *getVarFromExpr(const Expr *E) const {
      E = E ? E->IgnoreParenImpCasts() : nullptr;
      if (!E)
        return nullptr;
      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());
      if (const auto *UO = dyn_cast<UnaryOperator>(E))
        return getVarFromExpr(UO->getSubExpr());
      if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
        if (const VarDecl *V = getVarFromExpr(BO->getLHS()))
          return V;
        return getVarFromExpr(BO->getRHS());
      }
      return nullptr;
    }

    void noteUse(const Expr *E, const Stmt *S) {
      const VarDecl *V = getVarFromExpr(E);
      if (!V)
        return;
      Uses.push_back({dyn_cast<DeclRefExpr>(E->IgnoreParenImpCasts()), dyn_cast<const Expr>(S), V, NextOrder++});
    }

    void checkCondition(const Expr *E) {
      const auto *DRE = dyn_cast_or_null<DeclRefExpr>(E->IgnoreParenImpCasts());
      if (!DRE)
        return;
      if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
        CheckedVars.insert(VD);
    }

    void checkExpr(const Expr *E, const VarDecl *AssignedVar) {
      if (!E)
        return;
      if (isAllocationCall(E)) {
        if (AssignedVar)
          AllocatedVars.insert(AssignedVar);
      }
      for (const Stmt *Child : E->children()) {
        if (const auto *ChildE = dyn_cast_or_null<Expr>(Child))
          checkExpr(ChildE, AssignedVar);
      }
    }

    std::set<const VarDecl *> AllocatedVars;
  };

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "禁止动态分配的指针变量未检查即使用", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

  static bool isMallocLikeCall(const Expr *E) {
    const auto *CE = dyn_cast_or_null<CallExpr>(E->IgnoreParenImpCasts());
    if (!CE)
      return false;
    const FunctionDecl *FD = CE->getDirectCallee();
    if (!FD)
      return false;
    StringRef Name = FD->getName();
    return Name == "malloc" || Name == "calloc" || Name == "realloc";
  }

  static const VarDecl *getTrackedVarFromExpr(const Expr *E) {
    if (!E)
      return nullptr;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl());
    return nullptr;
  }

  static bool isNullCheckCond(const Expr *E, const VarDecl *V) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == V;
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return UO->getOpcode() == UO_LNot &&
             isNullCheckCond(UO->getSubExpr(), V);
    if (const auto *BO = dyn_cast<BinaryOperator>(E)) {
      if (!BO->isComparisonOp())
        return false;
      return (isTrackedVarFromExpr(BO->getLHS()) == V &&
              BO->getRHS()->isNullPointerConstant(
                  E->getExprLoc(), Expr::NPC_ValueDependentIsNull)) ||
             (isTrackedVarFromExpr(BO->getRHS()) == V &&
              BO->getLHS()->isNullPointerConstant(
                  E->getExprLoc(), Expr::NPC_ValueDependentIsNull));
    }
    return false;
  }

  static bool isUseOfVar(const Expr *E, const VarDecl *V) {
    if (!E)
      return false;
    E = E->IgnoreParenImpCasts();
    if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
      return dyn_cast<VarDecl>(DRE->getDecl()) == V;
    if (const auto *UO = dyn_cast<UnaryOperator>(E))
      return isUseOfVar(UO->getSubExpr(), V);
    if (const auto *BO = dyn_cast<BinaryOperator>(E))
      return isUseOfVar(BO->getLHS(), V) || isUseOfVar(BO->getRHS(), V);
    if (const auto *ME = dyn_cast<MemberExpr>(E))
      return isUseOfVar(ME->getBase(), V);
    if (const auto *ASE = dyn_cast<ArraySubscriptExpr>(E))
      return isUseOfVar(ASE->getBase(), V) || isUseOfVar(ASE->getIdx(), V);
    if (const auto *CE = dyn_cast<CallExpr>(E)) {
      for (const Expr *Arg : CE->arguments())
        if (isUseOfVar(Arg, V))
          return true;
    }
    return false;
  }

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    const Stmt *Body = FD->getBody();
    if (!Body)
      return;

    std::vector<const Stmt *> Stmts;
    llvm::SmallVector<const Stmt *, 32> Worklist;
    Worklist.push_back(Body);
    while (!Worklist.empty()) {
      const Stmt *S = Worklist.pop_back_val();
      Stmts.push_back(S);
      for (const Stmt *Child : S->children())
        if (Child)
          Worklist.push_back(Child);
    }

    std::set<const VarDecl *> Allocated;
    std::set<const VarDecl *> Checked;
    std::set<const VarDecl *> Reported;

    auto markAllocFromExpr = [&](const Expr *E) {
      const auto *BO = dyn_cast_or_null<BinaryOperator>(E);
      if (!BO || !BO->isAssignmentOp())
        return;
      const VarDecl *V = getTrackedVarFromExpr(BO->getLHS());
      if (!V)
        return;
      if (isMallocLikeCall(BO->getRHS()))
        Allocated.insert(V);
    };

    for (const Stmt *S : Stmts) {
      if (const auto *DS = dyn_cast<DeclStmt>(S)) {
        for (const Decl *DD : DS->decls()) {
          const auto *VD = dyn_cast<VarDecl>(DD);
          if (!VD)
            continue;
          if (const Expr *Init = VD->getInit())
            if (isMallocLikeCall(Init))
              Allocated.insert(VD);
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(S))
        markAllocFromExpr(cast<Expr>(S));

      if (const auto *IS = dyn_cast<IfStmt>(S)) {
        const Expr *Cond = IS->getCond();
        if (const auto *V = getTrackedVarFromExpr(Cond))
          Checked.insert(V);
      } else if (const auto *WS = dyn_cast<WhileStmt>(S)) {
        if (const auto *V = getTrackedVarFromExpr(WS->getCond()))
          Checked.insert(V);
      } else if (const auto *FS = dyn_cast<ForStmt>(S)) {
        if (const Expr *Cond = FS->getCond())
          if (const auto *V = getTrackedVarFromExpr(Cond))
            Checked.insert(V);
      } else if (const auto *DS = dyn_cast<DoStmt>(S)) {
        if (const auto *V = getTrackedVarFromExpr(DS->getCond()))
          Checked.insert(V);
      }

      for (const VarDecl *V : Allocated) {
        if (Reported.count(V))
          continue;

        bool HasCheckBeforeUse = false;
        for (const Stmt *Later : Stmts) {
          if (Later == S)
            continue;
          if (const auto *IFS = dyn_cast<IfStmt>(Later)) {
            if (isNullCheckCond(IFS->getCond(), V)) {
              HasCheckBeforeUse = true;
              continue;
            }
          }
          if (isUseOfVar(dyn_cast_or_null<Expr>(Later), V)) {
            if (!HasCheckBeforeUse) {
              emitASTReport(Later, AM.getAnalysisDeclContext(), BR);
              Reported.insert(V);
            }
            break;
          }
        }
      }
    }
  }
};
} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
Known compiling implementation template:
#include <memory>

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
class GeneratedUseUncheckPointerAfterMallocChecker : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  void emitASTReport(const Stmt *Violation, AnalysisDeclContext *ADC,
                     BugReporter &BR) const {
    PathDiagnosticLocation Location(Violation->getBeginLoc(),
                                    BR.getSourceManager());
    auto Report = std::make_unique<BasicBugReport>(
        BT, "Replace with the required diagnostic text", Location);
    Report->addRange(Violation->getSourceRange());
    Report->setDeclWithIssue(ADC->getDecl());
    BR.emitReport(std::move(Report));
  }

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
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc", "Generated GJB8114 checker");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;

When uncertain, restore the template's include set, registration functions,
BugReport construction, and class placement.
For check::ASTCodeBody, use BasicBugReport with PathDiagnosticLocation exactly
as demonstrated. Do not construct PathSensitiveBugReport and do not fabricate
or pass a null ExplodedNode.
Return exactly one C++ implementation in a fenced cpp code block. Do not
generate or include a project-local header.
