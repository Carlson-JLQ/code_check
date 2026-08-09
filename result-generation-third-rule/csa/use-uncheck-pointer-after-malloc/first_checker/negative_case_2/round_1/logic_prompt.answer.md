I’m extracting the rule into detection units and keeping them scoped to CSA-relevant patterns: allocation origin, first-use ordering, null-check forms, and the one-warning-per-variable constraint.[
  {
    "intent": "Detect a local pointer returned by dynamic allocation that is used before any null check.",
    "trigger": "A variable assigned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed by value, or otherwise used on a path before any explicit or implicit null comparison involving that same variable.",
    "constraints": [
      "The null check must occur before the first use; a later check does not suppress the violation.",
      "Accept `if (ptr != NULL)`, `if (ptr)`, `if (!ptr)` and equivalent null-pointer comparisons as valid checks.",
      "If the allocated pointer is never used, do not report.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "ExprEngine",
      "SymbolRef",
      "SVal",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "NonNull",
      "Null",
      "checkBind",
      "checkLocation",
      "checkPreStmt",
      "checkPostStmt"
    ]
  },
  {
    "intent": "Detect a dynamically allocated pointer that is checked only after it has already been used.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is first consumed in any dereference or dereference-like operation, and only later compared against null on the same execution path.",
    "constraints": [
      "The rule is violated even if a null check appears later in the same function.",
      "The check must precede the first use; ordering is the deciding factor.",
      "Accept shorthand checks such as `if (ptr)` and `if (!ptr)` as null checks.",
      "Emit only one diagnostic for that pointer variable."
    ],
    "csa_api_search_terms": [
      "checkBranchCondition",
      "assume",
      "ProgramState",
      "SymbolRef",
      "SValBuilder",
      "isNull",
      "isNonNull",
      "Load",
      "Store",
      "UnaryOperator",
      "BinaryOperator"
    ]
  },
  {
    "intent": "Detect use of a dynamically allocated global pointer without a prior null check.",
    "trigger": "A global pointer variable is assigned from `malloc`, `calloc`, or `realloc` and then used before any null comparison of that global on the path.",
    "constraints": [
      "The rule applies equally to global and local variables.",
      "The check must be on the same pointer variable that was allocated.",
      "If the global pointer is never used, do not report.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "GlobalVariable",
      "VarRegion",
      "MemRegion",
      "malloc",
      "calloc",
      "realloc",
      "checkLocation",
      "checkBind",
      "checkPreStmt",
      "SymbolRef",
      "StoreManager"
    ]
  },
  {
    "intent": "Detect use of a reallocated pointer without rechecking it after `realloc`.",
    "trigger": "A pointer previously allocated or already in use is passed to `realloc`, and the resulting pointer value is used before any fresh null check after the reallocation.",
    "constraints": [
      "A prior check before the earlier allocation or earlier use is not sufficient; the pointer must be checked again after `realloc`.",
      "If the pointer is not used after the reallocation, do not report.",
      "Accept explicit and implicit null checks as valid rechecks.",
      "Only one warning should be emitted for the violating pointer variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "malloc",
      "calloc",
      "SymbolReaper",
      "SymbolRef",
      "RegionStore",
      "checkPostCall",
      "checkBind",
      "checkPreStmt",
      "checkDeadSymbols",
      "assume"
    ]
  },
  {
    "intent": "Recognize valid early null-check patterns that suppress the rule.",
    "trigger": "A pointer from dynamic allocation is immediately compared against null before any use, including forms like `if (ptr != NULL)`, `if (ptr)`, `if (!ptr)`, or equivalent control-flow conditions.",
    "constraints": [
      "The check must dominate the first use of the pointer.",
      "The check may be explicit or implicit, as long as it constrains the pointer to non-null before use.",
      "Do not warn when the pointer is allocated and then unused.",
      "Do not warn when the pointer is reallocated but never used after the reallocation."
    ],
    "csa_api_search_terms": [
      "BranchCondition",
      "assume",
      "SVal",
      "NonNull",
      "Null",
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "PointerType",
      "ConstraintManager"
    ]
  }
]