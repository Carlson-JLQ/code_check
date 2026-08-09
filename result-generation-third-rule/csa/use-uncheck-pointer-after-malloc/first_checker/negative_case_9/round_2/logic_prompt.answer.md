I’m extracting the rule into discrete checker units and aligning them to the negative example, then I’ll return a strict JSON array with the required fields only.[
  {
    "intent": "Report a dynamically allocated pointer variable that is dereferenced or otherwise used before any null check has occurred after the allocation.",
    "trigger": "A value returned by `malloc`, `calloc`, or `realloc` is assigned to a pointer, and that pointer is used before an explicit or implicit null check on the same allocation instance.",
    "constraints": [
      "The null check must occur before the first use of the allocated pointer.",
      "Accept explicit checks like `if (ptr != NULL)` and `if (ptr == NULL)` as well as implicit checks like `if (ptr)` and `if (!ptr)`.",
      "If the pointer is never used after allocation, do not report.",
      "If the pointer is reallocated, require a fresh null check before any later use of the new value.",
      "Apply the rule equally to local and global variables.",
      "Only emit one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "DeclRefExpr",
      "IfStmt",
      "BranchCondition",
      "SVal",
      "ProgramState",
      "SymbolRef"
    ]
  },
  {
    "intent": "Report use of a global pointer obtained from dynamic allocation when the first use happens before any null check.",
    "trigger": "A global variable is assigned from `malloc`, `calloc`, or `realloc`, and then dereferenced or otherwise consumed before a null-check branch guards it.",
    "constraints": [
      "Global scope does not exempt the pointer from the check requirement.",
      "The first observable use after allocation is the violation point if no prior check exists.",
      "Do not report if the global pointer is allocated and never used.",
      "Do not report again for the same global pointer variable after the first violation has been emitted."
    ],
    "csa_api_search_terms": [
      "VarDecl",
      "GlobalVar",
      "StoreManager",
      "MemRegion",
      "ElementRegion",
      "FieldRegion",
      "Bind",
      "Load",
      "Dereference",
      "malloc",
      "calloc",
      "realloc"
    ]
  },
  {
    "intent": "Report cases where a null check exists only after the allocated pointer has already been used.",
    "trigger": "A pointer from dynamic allocation is dereferenced or passed to a use site, and a null comparison appears only later in control flow or later statements.",
    "constraints": [
      "The check must precede the first use; post-use checks do not satisfy the rule.",
      "Allow both explicit and shorthand null checks, but only if they dominate the use.",
      "Ignore later checks if the pointer has already been used without prior validation.",
      "One warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "CFG",
      "PathSensitiveBugReport",
      "PostStmt",
      "BranchNode",
      "Assume",
      "ConstraintManager",
      "ProgramPoint",
      "Store",
      "Load"
    ]
  },
  {
    "intent": "Report use of dynamically allocated pointers returned by `calloc` or `realloc` without a prior null check.",
    "trigger": "The result of `calloc` or `realloc` is assigned to a pointer and that pointer is used before any check guarding the new value.",
    "constraints": [
      "Treat `calloc` and `realloc` the same as `malloc` for the pre-use null-check requirement.",
      "For `realloc`, the check must be redone after reassignment because the returned pointer value can change.",
      "If `realloc` is not subsequently used, do not report.",
      "Do not duplicate reports for repeated uses of the same violating pointer."
    ],
    "csa_api_search_terms": [
      "calloc",
      "realloc",
      "CallExpr",
      "ReturnValue",
      "SymbolRef",
      "RegionState",
      "CheckBranch",
      "NullPointer",
      "NonNull"
    ]
  },
  {
    "intent": "Verify that a pointer guarded by a null check before first use is considered compliant.",
    "trigger": "A pointer returned by dynamic allocation is checked with a valid null test before any dereference or other use, and only used on the non-null path.",
    "constraints": [
      "Accept forms such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)` with the appropriate control-flow interpretation.",
      "The check must dominate the first use on the path that uses the pointer.",
      "No warning should be emitted for compliant allocation-and-check patterns.",
      "Do not require a specific style of comparison as long as it establishes a null guard."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BranchCondition",
      "ConditionTruthVal",
      "assume",
      "Nullness",
      "ProgramState",
      "SVal",
      "SymbolicValue"
    ]
  },
  {
    "intent": "Verify that an allocated pointer not used after allocation is not reported.",
    "trigger": "A pointer is returned by `malloc`, `calloc`, or `realloc`, but no dereference, access, or other use follows.",
    "constraints": [
      "Allocation alone is not a violation.",
      "The absence of a null check is tolerated if the pointer is never used.",
      "This applies to both local and global variables.",
      "A later reallocation without use is also non-violating."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "DeadSymbols",
      "LiveVariables",
      "ExprEngine",
      "SymbolReaper",
      "ExplodedNode"
    ]
  }
]