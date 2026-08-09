I’m extracting the rule into detection units and keeping them tightly aligned to the CSA behaviors implied by the examples. Next I’ll format them as JSON only, with each unit covering one actionable pattern.[
  {
    "intent": "Detect direct use of a pointer returned by `malloc` before any prior null check on that pointer.",
    "trigger": "A variable assigned from `malloc` is dereferenced or otherwise used before an `if (ptr != NULL)`, `if (ptr)`, or `if (!ptr)`-style check guarding that use.",
    "constraints": [
      "The null check must occur before the first use; a check after the use still violates the rule.",
      "Only report when the allocated pointer is actually used; allocation alone is not a violation.",
      "Apply the rule to both local and global variables.",
      "Report only one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "malloc",
      "CallExpr",
      "DeclRefExpr",
      "UnaryOperator",
      "BinaryOperator",
      "isNullPointerConstant",
      "PointerArithmetic",
      "RegionStore",
      "SVal"
    ]
  },
  {
    "intent": "Detect use of a `calloc`-returned pointer before any prior null check.",
    "trigger": "A variable assigned from `calloc` is dereferenced or otherwise used before a preceding null check on that variable.",
    "constraints": [
      "A null check after the first use does not satisfy the rule.",
      "If the pointer is never used, no warning should be emitted.",
      "Accept explicit and implicit null checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "Apply uniformly to local and global variables.",
      "Emit at most one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "calloc",
      "CallExpr",
      "DeclRefExpr",
      "UnaryOperator",
      "BinaryOperator",
      "isNullPointerConstant",
      "SVal",
      "RegionState"
    ]
  },
  {
    "intent": "Detect use of a `realloc`-returned pointer before a fresh null check after reallocation.",
    "trigger": "A pointer updated by `realloc` is used before being checked again for non-null after the reallocation call.",
    "constraints": [
      "A pointer must be checked again after each `realloc` before any subsequent use.",
      "A null check that happened before the `realloc` call does not count for the reallocated result.",
      "If the pointer is never used after reallocation, no warning should be emitted.",
      "The rule applies to both local and global variables.",
      "Report only one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "realloc",
      "CallExpr",
      "DeclRefExpr",
      "UnaryOperator",
      "BinaryOperator",
      "isNullPointerConstant",
      "MemRegion",
      "SymbolRef"
    ]
  },
  {
    "intent": "Detect unsafe use of a global pointer initialized from dynamic allocation before any prior null check.",
    "trigger": "A global variable assigned from `malloc`, `calloc`, or `realloc` is used before a null check on that global variable.",
    "constraints": [
      "Global storage must be tracked the same as local storage.",
      "The check must precede the first use of the global pointer.",
      "A post-use check is still a violation.",
      "Do not warn if the global allocation result is never used.",
      "Only one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "VarDecl",
      "GlobalVariable",
      "malloc",
      "calloc",
      "realloc",
      "DeclRefExpr",
      "isNullPointerConstant",
      "SVal"
    ]
  },
  {
    "intent": "Detect null-checks that occur too late, after the dynamically allocated pointer has already been used.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is first used, and only afterward appears in a null check.",
    "constraints": [
      "The ordering matters: the check must come before the first use.",
      "This includes shorthand checks such as `if (ptr)` and `if (!ptr)` as valid checks only when they occur before use.",
      "A late check does not suppress the violation.",
      "One warning per pointer variable, even if used multiple times before the late check."
    ],
    "CSA API search terms": [
      "PostStmt",
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "DeclRefExpr",
      "malloc",
      "calloc",
      "realloc"
    ]
  },
  {
    "intent": "Detect any first use of a dynamically allocated pointer without a preceding explicit or implicit null comparison.",
    "trigger": "The pointer is dereferenced, indexed, assigned through, or otherwise consumed before a null comparison is observed on that variable.",
    "constraints": [
      "Recognize both explicit comparisons against `NULL` and implicit truthiness tests.",
      "Do not report when allocation result is never used.",
      "Do not report when the first use occurs only after a passing null check.",
      "Track the rule across control flow for both locals and globals.",
      "Limit to a single warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "BranchCondition",
      "IfStmt",
      "ConditionalOperator",
      "UnaryOperator",
      "BinaryOperator",
      "NullPointerConstant",
      "PointerDereference",
      "Store"
    ]
  }
]