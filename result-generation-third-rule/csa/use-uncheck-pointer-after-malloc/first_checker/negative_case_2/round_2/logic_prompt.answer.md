I’m extracting the checker logic into discrete detection units and mapping each one to trigger/constraint/search terms that a CSA implementation can search for.[
  {
    "intent": "Detect use of a pointer returned by dynamic memory allocation before any null-check has been performed on that pointer.",
    "trigger": "A value from `malloc`, `calloc`, or `realloc` is assigned to a pointer variable and that same variable is dereferenced, indexed, passed as a non-null argument, or otherwise used before any null comparison/conditional guard appears on the execution path.",
    "constraints": [
      "The null-check must occur before the first use to suppress a warning.",
      "Accept explicit and implicit checks, including `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)` patterns used to guard the non-null path.",
      "A check performed after the first use does not satisfy the rule.",
      "If the allocated pointer is never used, do not warn.",
      "Report only one warning per violating pointer variable.",
      "Apply the same rule to local and global variables."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "UnaryOperator",
      "BinaryOperator",
      "Stmt::isNullPointerConstant",
      "Expr::isNullPointerConstant",
      "ImplicitCastExpr",
      "IfStmt",
      "DeclRefExpr",
      "MemRegion",
      "VarRegion",
      "SVal",
      "LocationContext"
    ]
  },
  {
    "intent": "Detect delayed null-check patterns where the first use of an allocated pointer occurs before the first null guard.",
    "trigger": "The pointer is used in any expression or statement prior to a subsequent `if`, `while`, `assert`, or equivalent null check that references the same allocation result.",
    "constraints": [
      "A post-use null check is still a violation.",
      "The checker should follow the first observable use, not the first syntactic appearance of a check.",
      "Handle shorthand guards and negated guards equivalently when they protect later uses.",
      "Do not emit multiple diagnostics for repeated uses of the same already-violating pointer."
    ],
    "csa_api_search_terms": [
      "PreStmt",
      "PostStmt",
      "check::Location",
      "check::Bind",
      "check::PreCall",
      "check::DeadSymbols",
      "BranchCondition",
      "ProgramState",
      "SymbolRef",
      "ConstraintManager",
      "assume"
    ]
  },
  {
    "intent": "Detect use of dynamically allocated global variables before a null-check after assignment.",
    "trigger": "A global pointer variable receives a result from `malloc`, `calloc`, or `realloc`, and later code dereferences or otherwise uses that global before any null-check on that global pointer has occurred.",
    "constraints": [
      "Global storage is in scope for the same rule as local storage.",
      "The check must guard the global pointer prior to first use.",
      "A global pointer that is assigned but never used must not trigger a warning.",
      "Only one warning per global pointer variable is allowed."
    ],
    "csa_api_search_terms": [
      "GlobalRegion",
      "VarRegion",
      "MemRegion",
      "DeclRefExpr",
      "Load",
      "Store",
      "SymbolRef",
      "ProgramState",
      "RegionStore",
      "SValBuilder"
    ]
  },
  {
    "intent": "Require a fresh null-check after pointer reallocation before any subsequent use.",
    "trigger": "A pointer previously obtained from dynamic allocation is passed to `realloc`, the returned value is stored back into the same pointer variable or another tracked variable, and the new value is used before a new null-check on the reallocated result.",
    "constraints": [
      "A prior check on the original allocation does not satisfy the post-realloc requirement.",
      "The reallocated result must be checked again before the next use.",
      "If the reallocated pointer is never used afterward, do not warn.",
      "Treat `realloc` as producing a potentially new allocation result that resets the null-check obligation.",
      "Only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "ReturnStmt",
      "SymbolReaper",
      "SymbolRef",
      "Store",
      "Load",
      "ProgramState",
      "check::PostCall",
      "check::PreStmt"
    ]
  },
  {
    "intent": "Recognize acceptable null-check idioms that satisfy the rule before use.",
    "trigger": "The allocated pointer is tested with any standard null-check form before its first use, and all subsequent uses are dominated by the non-null branch.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr == NULL)` with use only on the non-null branch, `if (ptr)`, and `if (!ptr)` with use only after the negated condition is handled correctly.",
      "The check must be semantically tied to the same pointer variable returned by allocation or reallocation.",
      "A check on another variable or an unrelated expression does not count.",
      "This unit is for suppression logic, not for emitting warnings."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "isNullPointerConstant",
      "ConstraintManager",
      "assume",
      "BranchCondition",
      "ProgramState"
    ]
  },
  {
    "intent": "Suppress diagnostics when a dynamically allocated pointer is never used.",
    "trigger": "A pointer is assigned the result of `malloc`, `calloc`, or `realloc`, but no dereference, call argument use, arithmetic use, or other meaningful use occurs afterward.",
    "constraints": [
      "Allocation alone is not a violation.",
      "Do not require a null-check if there is no use.",
      "This applies to both local and global pointers.",
      "Do not emit a warning merely because the allocation result was not checked."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "SymbolReaper",
      "DeadSymbols",
      "RegionStore",
      "VarRegion",
      "MemRegion",
      "Stmt",
      "Expr",
      "CallExpr"
    ]
  }
]