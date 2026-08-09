[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any successful null check on that allocation result.",
    "trigger": "A value from `malloc`, `calloc`, or `realloc` is assigned to a pointer variable and that same pointer is dereferenced, passed to a sink that uses it, or otherwise read/written before any prior null comparison or equivalent guard.",
    "constraints": [
      "The null check must occur before the first use; checking after use is a violation.",
      "Accept explicit and implicit checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not report a violation.",
      "Report only one warning per violating pointer variable.",
      "Apply the rule to both local and global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "UnaryOperator",
      "BinaryOperator",
      "IfStmt",
      "DeclRefExpr",
      "ImplicitCastExpr",
      "isNullPointerConstant",
      "canIgnoreParenImpCasts",
      "RegionState",
      "ProgramState",
      "checkPostStmt<CallExpr>",
      "checkLocation",
      "checkPreStmt<UnaryOperator>",
      "checkPreStmt<BinaryOperator>"
    ]
  },
  {
    "intent": "Treat allocation followed by immediate null guarding as compliant until the guarded branch proves the pointer is non-null.",
    "trigger": "After a dynamic allocation call, the code performs a guard that rejects or branches on null before any dereference or use, and later uses the pointer only on the non-null path.",
    "constraints": [
      "The guard may be explicit or shorthand.",
      "The first use must be control-dependent on the null check result.",
      "Do not flag code where the pointer is only used inside the non-null branch.",
      "Handle local and global storage uniformly."
    ],
    "csa_api_search_terms": [
      "ConditionBRVisitor",
      "BranchCondition",
      "assume",
      "assumeDual",
      "checkBranchCondition",
      "IfStmt",
      "WhileStmt",
      "ForStmt",
      "SwitchStmt",
      "exploded graph",
      "ProgramState",
      "SVal"
    ]
  },
  {
    "intent": "Detect late null checks where the allocated pointer has already been used once.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is dereferenced or otherwise used before the first null check, and a null check appears only afterward.",
    "constraints": [
      "A later null check does not repair an earlier violation.",
      "The report should be tied to the first unsafe use, not the later check.",
      "Only one diagnostic should be emitted for the pointer variable even if there are multiple unsafe uses before the check."
    ],
    "csa_api_search_terms": [
      "checkLocation",
      "Bind",
      "Store",
      "load",
      "RegionBindings",
      "MemRegion",
      "SymbolRef",
      "Deref",
      "UnaryOperator",
      "ArraySubscriptExpr"
    ]
  },
  {
    "intent": "Detect unsafe use of dynamically allocated global variables.",
    "trigger": "A global pointer is assigned a dynamic allocation result and then used before any null guard, including use from another function or translation unit context tracked within the analysis path.",
    "constraints": [
      "Global scope does not exempt the variable from the null-check requirement.",
      "A check in one function must precede the first use in the relevant path.",
      "Do not emit repeated warnings for the same global pointer variable."
    ],
    "csa_api_search_terms": [
      "VarDecl",
      "GlobalVarRegion",
      "ElementRegion",
      "FieldRegion",
      "MemRegion",
      "LocationContext",
      "SymbolRef",
      "checkBind",
      "checkLocation",
      "checkPostCall"
    ]
  },
  {
    "intent": "Require a fresh null check after reassignment by reallocation before any subsequent use.",
    "trigger": "A pointer previously allocated or already checked is assigned the result of `realloc`, and that new value is used before a new null check on the post-reallocation value.",
    "constraints": [
      "The reallocated result must be checked again even if the original allocation had been checked.",
      "If `realloc` succeeds or the pointer is not used afterward, do not report.",
      "The rule applies to both local and global variables.",
      "One warning per pointer variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "checkPostCall",
      "Store",
      "SymbolReaper",
      "RegionState",
      "ProgramState",
      "isReleased",
      "MallocChecker",
      "CString",
      "conjureSymbolVal"
    ]
  },
  {
    "intent": "Accept null-check-only code paths as non-violations when no dereference or meaningful use occurs.",
    "trigger": "A pointer from dynamic allocation is checked for null but never dereferenced, indexed, or otherwise used on any path.",
    "constraints": [
      "Do not report just because allocation occurred without use.",
      "A null check alone is sufficient for compliance if no subsequent use exists.",
      "Avoid false positives on dead stores or unused allocated pointers."
    ],
    "csa_api_search_terms": [
      "DeadSymbols",
      "checkDeadSymbols",
      "checkEndFunction",
      "SymbolRef",
      "SVal",
      "isUndef",
      "isUnknown",
      "StoreManager",
      "RegionStore",
      "Expr"
    ]
  }
]