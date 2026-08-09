I’m extracting the checker units from the rule and the negative test, then I’ll format them as strict JSON with the four fields you asked for.[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any prior null check, and emit one warning for that pointer variable when it is used unsafely.",
    "trigger": "A pointer value originating from `malloc`, `calloc`, or `realloc` is dereferenced, passed as a used argument, or otherwise consumed before an earlier null check on that same allocation result.",
    "constraints": [
      "The null check must occur before the first use; a check after use is still a violation.",
      "Accept explicit and implicit null checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not report a violation.",
      "If the pointer is reallocated, require a new null check before any subsequent use.",
      "Apply the rule to both local and global variables.",
      "Report at most one warning per violating pointer variable."
    ],
    "CSA_API_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "UnaryOperator",
      "BinaryOperator",
      "ImplicitCastExpr",
      "DeclRefExpr",
      "IfStmt",
      "isNullPointerConstant",
      "SVal",
      "MemRegion",
      "VarDecl"
    ]
  },
  {
    "intent": "Flag the negative case where a dynamically allocated pointer is used immediately and the null check appears only afterward.",
    "trigger": "A statement like `*p = 1;` occurs after `p = malloc(...)` and before `if (p == nullptr)` or any equivalent null comparison.",
    "constraints": [
      "The first observed use establishes the violation if no prior check exists.",
      "A later `nullptr` or `NULL` comparison does not cure the earlier unsafe use.",
      "The test should still pass even if the code returns after the late check.",
      "Treat `nullptr` and `NULL` as equivalent null-check forms for C and C++ inputs."
    ],
    "CSA_API_search_terms": [
      "check::PreStmt",
      "check::PostStmt",
      "BinaryOperator",
      "UnaryOperator",
      "Dereference",
      "CXXNullPtrLiteralExpr",
      "IntegerLiteral",
      "IfStmt"
    ]
  },
  {
    "intent": "Verify that a pointer returned from allocation is considered safe only when a null check occurs before use.",
    "trigger": "An allocation result is immediately guarded by `if (ptr)` or `if (ptr != NULL)` before any dereference or member access.",
    "constraints": [
      "The checker must treat the guarded branch as compliant only when the use is dominated by the check.",
      "Short-circuit and shorthand forms of null checks are valid.",
      "Do not report when the pointer is never used after allocation.",
      "Do not report when control flow exits before any use after a failed check."
    ],
    "CSA_API_search_terms": [
      "IfStmt",
      "BranchCondition",
      "BinaryOperator",
      "UnaryOperator",
      "NULL",
      "nullptr",
      "ExprEngine",
      "CFG"
    ]
  },
  {
    "intent": "Handle global allocation results the same way as local variables when checking for prior null validation.",
    "trigger": "A global pointer assigned from dynamic allocation is used before a null check, such as a global `p` being written through or read from after allocation without guarding it first.",
    "constraints": [
      "Global storage duration does not exempt the pointer from the rule.",
      "Track the allocation origin through assignments to globals and subsequent uses.",
      "The warning should still be limited to one per violating global pointer variable."
    ],
    "CSA_API_search_terms": [
      "VarDecl",
      "GlobalVar",
      "DeclRefExpr",
      "BinaryOperator",
      "StoreManager",
      "RegionStore",
      "MemRegion"
    ]
  },
  {
    "intent": "Require a fresh null check after `realloc` before any later use of the returned pointer.",
    "trigger": "A pointer result from `realloc` is used without a preceding null check after the reallocation call.",
    "constraints": [
      "A prior check for the pre-realloc pointer does not automatically satisfy the post-realloc requirement.",
      "If the pointer is never used after `realloc`, do not report.",
      "Preserve the same one-warning-per-variable behavior across repeated reallocations."
    ],
    "CSA_API_search_terms": [
      "realloc",
      "CallEvent",
      "PostCall",
      "BinaryOperator",
      "IfStmt",
      "MemRegion",
      "SVal"
    ]
  }
]