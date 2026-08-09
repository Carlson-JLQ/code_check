I’m extracting the checker logic into structured units and aligning them to the negative test and rule text. Next I’m formatting the result as strict JSON only, with no extra prose.[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any non-null check has occurred for that allocation result.",
    "trigger": "A pointer assigned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed as a non-checked argument, or otherwise used before an earlier null check on that same allocation result.",
    "constraints": [
      "The null check must happen before the first use.",
      "Accept explicit and implicit checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the pointer is never used after allocation, do not report.",
      "Report only once per violating pointer variable.",
      "Applies to local and global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "PointerDereference",
      "ArraySubscript",
      "BinaryOperator",
      "UnaryOperator",
      "checkNull",
      "assume",
      "SVal",
      "LocationContext",
      "VarDecl"
    ]
  },
  {
    "intent": "Detect late null checks that occur only after a dynamically allocated pointer has already been used.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is first used, and only afterward is there a null check on that same pointer.",
    "constraints": [
      "A check after use does not satisfy the rule.",
      "The first use is what matters for violation detection.",
      "A later check does not retroactively validate earlier uses.",
      "Report only one warning for the pointer variable even if it is used multiple times before the check."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "IfStmt",
      "Condition",
      "BranchCondition",
      "ExplodedGraph",
      "ProgramState",
      "SymbolRef",
      "SValBuilder"
    ]
  },
  {
    "intent": "Detect use of a dynamically allocated global variable before a required null check.",
    "trigger": "A global pointer is assigned from `malloc`, `calloc`, or `realloc` and then used before any valid null check.",
    "constraints": [
      "Global storage does not change the rule.",
      "The check must still precede first use.",
      "Only one warning should be emitted for the offending global variable.",
      "Do not warn if the global allocation result is never used."
    ],
    "csa_api_search_terms": [
      "GlobalVarDecl",
      "VarDecl",
      "malloc",
      "calloc",
      "realloc",
      "PointerDereference",
      "DeclRefExpr",
      "ProgramState",
      "SymbolRef"
    ]
  },
  {
    "intent": "Require a fresh null check after reallocation before any subsequent use of the possibly moved result.",
    "trigger": "A pointer is passed through `realloc` and the resulting pointer is used before being checked for null again.",
    "constraints": [
      "A prior check on an older allocation result does not satisfy the post-`realloc` requirement.",
      "The new allocation result from `realloc` must be checked before use.",
      "If the reallocated pointer is never used, do not report.",
      "Only one warning per variable should be emitted."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "ReturnStmt",
      "Assignment",
      "SymbolRef",
      "ProgramState",
      "PointerDereference",
      "ArraySubscript",
      "checkNull"
    ]
  },
  {
    "intent": "Recognize acceptable null-check patterns that satisfy the rule before first use.",
    "trigger": "The code tests the allocation result with explicit or implicit null comparison before any use, including forms like `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
    "constraints": [
      "The accepted check must dominate the first use.",
      "Equivalent null-comparison forms should be treated as valid.",
      "The rule is satisfied only if the use is guarded by the check outcome.",
      "Do not require a specific syntax shape for the null test."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "NULL",
      "checkNull",
      "Condition",
      "assume"
    ]
  },
  {
    "intent": "Suppress reports for allocation results that are never used.",
    "trigger": "A pointer is obtained from dynamic allocation but there is no dereference, indexing, member access, or other use afterward.",
    "constraints": [
      "No warning should be emitted for unused allocation results.",
      "The absence of a use means the rule is not violated.",
      "This applies equally to local and global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "DeadSymbols",
      "SymbolRef",
      "VarDecl",
      "ProgramState"
    ]
  }
]