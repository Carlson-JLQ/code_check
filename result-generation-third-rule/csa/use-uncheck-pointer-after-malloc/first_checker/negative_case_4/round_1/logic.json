[
  {
    "intent": "Detect first use of a pointer returned by dynamic allocation without any prior null check.",
    "trigger": "A value returned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed as a non-null argument, or otherwise used before any null check on that pointer has executed.",
    "constraints": [
      "The null check must occur before the first use; a check after first use is a violation.",
      "Accept explicit and implicit checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the pointer is never used after allocation, do not report.",
      "Only one warning should be emitted per violating pointer variable."
    ],
    "CSA API search terms": [
      "MallocChecker",
      "CallEvent",
      "CallExpr",
      "VarDecl",
      "RegionState",
      "ProgramState",
      "SVal",
      "SymbolRef",
      "checkPostCall",
      "checkLocation",
      "checkBind",
      "assume",
      "ExprEngine"
    ]
  },
  {
    "intent": "Detect a null check that happens only after the allocated pointer has already been used.",
    "trigger": "A pointer from dynamic allocation is used first, and a later conditional null test on the same pointer appears afterward in the control flow.",
    "constraints": [
      "Post-use checks do not satisfy the rule.",
      "The checker must track order of events within a path, not just the presence of a check anywhere in the function.",
      "Handle both local and global variables."
    ],
    "CSA API search terms": [
      "checkPreStmt",
      "checkPostStmt",
      "BranchCondition",
      "BinaryOperator",
      "UnaryOperator",
      "ProgramState",
      "ExplodedNode",
      "ConstraintManager",
      "SValBuilder",
      "assume"
    ]
  },
  {
    "intent": "Detect use of a global pointer variable after dynamic allocation without a prior null check.",
    "trigger": "A global variable is assigned the result of `malloc`, `calloc`, or `realloc`, then used before any null check on that same variable.",
    "constraints": [
      "Global storage must be tracked the same as local storage.",
      "A check on another alias or unrelated variable does not satisfy the requirement unless it proves the allocated pointer itself is non-null.",
      "Report only once per violating variable even if it is used multiple times."
    ],
    "CSA API search terms": [
      "GlobalRegion",
      "VarRegion",
      "MemRegion",
      "StoreManager",
      "ProgramState",
      "SymbolRef",
      "LocationContext",
      "checkBind",
      "checkLocation",
      "checkEndFunction"
    ]
  },
  {
    "intent": "Detect missing re-check after `realloc` before any subsequent use of the returned pointer.",
    "trigger": "A pointer that has been updated by `realloc` is used before a new null check on that reallocated value.",
    "constraints": [
      "Reallocation resets the safety requirement; the pointer must be checked again after `realloc`.",
      "Do not suppress the warning because the original allocation was checked earlier.",
      "If the reallocated pointer is never used, do not report.",
      "Only one warning per pointer variable."
    ],
    "CSA API search terms": [
      "ReallocChecker",
      "MallocChecker",
      "checkPostCall",
      "CallEvent",
      "ProgramState",
      "SymbolRef",
      "RegionState",
      "assume",
      "checkDeadSymbols"
    ]
  },
  {
    "intent": "Detect use of pointers from `calloc` or `realloc` without any prior null check.",
    "trigger": "A pointer returned by `calloc` or `realloc` is used before being tested for null.",
    "constraints": [
      "Treat `calloc` and `realloc` the same as `malloc` for this rule.",
      "Accept shorthand and explicit checks equally.",
      "A null check after the use is still a violation."
    ],
    "CSA API search terms": [
      "CallEvent",
      "CallExpr",
      "IdentifierInfo",
      "FunctionDecl",
      "MallocChecker",
      "ProgramState",
      "SymbolRef",
      "checkPostCall",
      "checkLocation"
    ]
  },
  {
    "intent": "Recognize valid null-check patterns that satisfy the rule before first use.",
    "trigger": "A pointer from dynamic allocation is guarded by a prior null test such as `if (ptr != NULL)`, `if (ptr)`, or `if (!ptr)` and only then used on the non-null path.",
    "constraints": [
      "The checker must understand both explicit comparison and implicit truthiness tests.",
      "The use must be dominated by the check on the same path.",
      "If the pointer is not used after the check, do not report."
    ],
    "CSA API search terms": [
      "BranchCondition",
      "BinaryOperator",
      "UnaryOperator",
      "Assume",
      "ProgramState",
      "ConstraintManager",
      "ExprEngine",
      "SValBuilder",
      "checkBranchCondition"
    ]
  }
]