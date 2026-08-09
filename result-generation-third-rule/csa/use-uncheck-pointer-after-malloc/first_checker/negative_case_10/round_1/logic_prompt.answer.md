[
  {
    "intent": "Detect use of a pointer returned by `malloc` before any non-null check has been performed on that pointer.",
    "trigger": "A variable assigned from `malloc` is dereferenced, passed as a non-null-required argument, or otherwise used in a way that requires a valid pointer before any preceding null check on that variable in the current allocation epoch.",
    "constraints": [
      "The null check must occur before the first use; a check after the first use does not satisfy the rule.",
      "Accept explicit and implicit null checks such as `ptr != NULL`, `ptr == NULL`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not report a violation.",
      "Apply this rule to both local and global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "CallExpr",
      "VarDecl",
      "UnaryOperator",
      "BinaryOperator",
      "ImplicitCastExpr",
      "if (ptr)",
      "if (!ptr)",
      "ptr != NULL",
      "null check before use"
    ]
  },
  {
    "intent": "Detect use of a pointer returned by `calloc` before any non-null check has been performed on that pointer.",
    "trigger": "A variable assigned from `calloc` is used before an earlier null check on that same variable exists.",
    "constraints": [
      "The check must precede the first use of the pointer.",
      "A later check after use is still a violation.",
      "If the pointer is never used after allocation, suppress the warning.",
      "Treat global and local variables the same way."
    ],
    "csa_api_search_terms": [
      "calloc",
      "CallExpr",
      "VarDecl",
      "BinaryOperator",
      "UnaryOperator",
      "IfStmt",
      "RegionStore",
      "null pointer comparison"
    ]
  },
  {
    "intent": "Detect use of a pointer returned by `realloc` before re-checking the new pointer value for non-null.",
    "trigger": "A variable assigned from `realloc` is used before a null check is performed after that reallocation assignment.",
    "constraints": [
      "A pointer must be checked again after `realloc` because the returned value may differ from the prior allocation state.",
      "Using the pointer after reallocation without a new prior check is a violation.",
      "If the pointer is not used after `realloc`, do not report.",
      "The same rule applies to local and global variables."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "AssignmentExpr",
      "VarDecl",
      "Realloc",
      "symbol rebind",
      "non-null check after realloc"
    ]
  },
  {
    "intent": "Treat dereference or member access as the first use event that must be guarded by a prior null check.",
    "trigger": "Operations such as `*ptr`, `ptr->field`, array indexing like `ptr[i]`, or passing the pointer to a function that requires a valid pointer occur before the first null check.",
    "constraints": [
      "The checker should model first-use ordering, not merely the existence of any check in the same function.",
      "A use before check is a violation even if a later `if (ptr)` appears.",
      "Only one warning should be emitted per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "UnaryOperator",
      "MemberExpr",
      "ArraySubscriptExpr",
      "CallExpr",
      "Dereference",
      "pointer use",
      "first use"
    ]
  },
  {
    "intent": "Recognize valid null-check patterns that satisfy the rule before pointer use.",
    "trigger": "A pointer obtained from dynamic allocation is tested with a standard null comparison before any use, and only used on the checked-success path.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr == NULL)`, `if (ptr)`, and `if (!ptr)` as valid checks.",
      "The use must be dominated by the branch where the pointer is known to be non-null.",
      "A check after use does not count."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "NULL",
      "non-null branch",
      "branch constraint"
    ]
  },
  {
    "intent": "Suppress diagnostics for allocated pointers that are never used.",
    "trigger": "A pointer receives the result of `malloc`, `calloc`, or `realloc`, but no later dereference, member access, indexing, or equivalent use occurs.",
    "constraints": [
      "Do not report a violation solely because the allocation result was not checked.",
      "The rule only applies when the pointer is actually used.",
      "This suppression must still work for global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "unused allocation",
      "no use",
      "dead store",
      "VarDecl"
    ]
  },
  {
    "intent": "Apply the same before-use null-check requirement to global variables holding dynamically allocated pointers.",
    "trigger": "A global pointer is assigned a dynamic allocation result and later used without a prior null check in the relevant allocation epoch.",
    "constraints": [
      "Global storage does not exempt the pointer from the rule.",
      "Track use across function boundaries when the global is read or dereferenced after allocation.",
      "Report only once per violating variable."
    ],
    "csa_api_search_terms": [
      "GlobalVarDecl",
      "VarDecl",
      "malloc",
      "calloc",
      "realloc",
      "global pointer",
      "cross-function use",
      "non-null check"
    ]
  },
  {
    "intent": "Emit at most one warning for each violating pointer variable, even if the variable is used multiple times without a prior check.",
    "trigger": "The same allocated pointer is used more than once before any valid null check, or used again after a failed or missing check.",
    "constraints": [
      "Deduplicate diagnostics by variable identity, not by each use site.",
      "The warning should point to the first violating use or the most relevant use site per checker policy.",
      "Subsequent uses of the same unguarded pointer should not produce additional warnings."
    ],
    "csa_api_search_terms": [
      "diagnostic deduplication",
      "symbol",
      "VarDecl",
      "ExplodedGraph",
      "ProgramState",
      "first violation",
      "single warning per variable"
    ]
  }
]