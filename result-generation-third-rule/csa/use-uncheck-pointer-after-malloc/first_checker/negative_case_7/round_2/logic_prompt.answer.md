I’m extracting the checker logic as structured units and grounding them in the negative test and rule text. I’ll keep it to JSON only, with each unit carrying intent, trigger, constraints, and CSA API search terms.[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any non-null check on that allocation result.",
    "trigger": "A pointer variable assigned from malloc, calloc, or realloc is dereferenced, indexed, passed as a live pointer argument, or otherwise used before any prior explicit or implicit null check on that same allocation result.",
    "constraints": [
      "The null check must occur before the first use; checking after use is still a violation.",
      "Accept explicit comparisons such as ptr != NULL and ptr == NULL, as well as implicit checks such as if (ptr) and if (!ptr).",
      "If the allocated pointer is never used, do not report.",
      "Report at most one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "CallEvent",
      "ExprEngine",
      "SVal",
      "SymbolRef",
      "BinaryOperator",
      "UnaryOperator",
      "BranchCondition",
      "check::PostCall",
      "check::Location",
      "check::PreStmt<BinaryOperator>"
    ]
  },
  {
    "intent": "Detect use of a calloc result without a prior null check, including cases where the check exists only after the first use.",
    "trigger": "A pointer assigned from calloc is used before an earlier guarding null test on that pointer value.",
    "constraints": [
      "A null test after the first use does not satisfy the rule.",
      "The rule applies to both local and global variables that receive the allocated value.",
      "If the calloc result is assigned to a variable and never used, do not report.",
      "Only one diagnostic should be emitted for the variable even if there are multiple later uses."
    ],
    "csa_api_search_terms": [
      "calloc",
      "MallocChecker",
      "MemRegion",
      "VarRegion",
      "StoreManager",
      "SValBuilder",
      "ConstraintManager",
      "Assume",
      "check::Bind",
      "check::BranchCondition"
    ]
  },
  {
    "intent": "Detect use of a realloc result without re-checking it after the reallocation event.",
    "trigger": "A pointer returned by realloc is used before a new null check on the post-realloc value, even if the original allocation had already been checked.",
    "constraints": [
      "A realloc produces a new allocation result that must be checked again before any subsequent use.",
      "If the pointer is reallocated and never used afterward, do not report.",
      "A prior check on the pre-realloc pointer does not count for the post-realloc result.",
      "Only one warning should be reported for the violating pointer variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "check::PostCall",
      "CallEvent",
      "SymbolRef",
      "Taint",
      "RegionStore",
      "PointerEscape",
      "DynamicMemoryModeling",
      "MallocChecker",
      "PreCall"
    ]
  },
  {
    "intent": "Allow safe patterns where allocation is followed immediately by a null guard before any use.",
    "trigger": "A pointer from malloc, calloc, or realloc is checked with an acceptable null test before its first dereference or other use, and only used on the non-null path.",
    "constraints": [
      "Accept both explicit and shorthand null checks, including if (ptr), if (!ptr), and ptr != NULL.",
      "A check that dominates all uses is valid.",
      "Do not report when the pointer is never used after allocation.",
      "Do not report when the pointer is reallocated but not used afterward."
    ],
    "csa_api_search_terms": [
      "BranchCondition",
      "Assume",
      "ConstraintManager",
      "SymbolRef",
      "BinaryOperator",
      "UnaryOperator",
      "check::BranchCondition",
      "check::PreStmt<IfStmt>",
      "MallocChecker"
    ]
  },
  {
    "intent": "Treat global variables holding dynamically allocated pointers the same as local variables.",
    "trigger": "A global pointer variable is assigned from malloc, calloc, or realloc and then used without a prior null check on that variable value.",
    "constraints": [
      "Global and local variables are subject to the same rule.",
      "The warning must be attached to the violating pointer variable, not to unrelated uses.",
      "Only the first violating use should produce a report for that variable.",
      "If the global pointer is checked before use, do not report."
    ],
    "csa_api_search_terms": [
      "GlobalRegion",
      "VarRegion",
      "MemRegion",
      "SVal",
      "Store",
      "RegionStore",
      "check::Bind",
      "check::Location",
      "MallocChecker"
    ]
  }
]