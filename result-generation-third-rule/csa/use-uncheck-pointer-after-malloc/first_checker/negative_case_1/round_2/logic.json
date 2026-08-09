[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any prior null check on that specific allocation result.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is dereferenced, passed to a sink, or otherwise used before an explicit or implicit null check occurs on that pointer value.",
    "constraints": [
      "The null check must happen before the first use.",
      "Accept `if (ptr != NULL)`, `if (ptr)`, `if (!ptr)`, and equivalent explicit or implicit comparisons.",
      "If the pointer is never used after allocation, do not report.",
      "Apply to local and global variables equally.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "dyn_cast<CallExpr>",
      "ExprEngine",
      "SVal",
      "SymbolRef",
      "BranchCondition",
      "ConstraintManager",
      "isNullPointerConstant"
    ]
  },
  {
    "intent": "Detect dereference or operational use of a dynamically allocated pointer when the code performs a null check only after the first use.",
    "trigger": "A pointer returned by allocation is used first, and a subsequent null comparison appears later in the same path.",
    "constraints": [
      "The post-use check does not satisfy the rule.",
      "Treat any first observable use as a violation, including dereference and argument use that depends on pointer validity.",
      "Only one diagnostic should be emitted for the variable even if multiple later checks exist."
    ],
    "csa_api_search_terms": [
      "checkPreStmt",
      "checkPostStmt",
      "checkLocation",
      "StoreManager",
      "load",
      "BindExpr",
      "UnaryOperator",
      "BinaryOperator",
      "PointerType"
    ]
  },
  {
    "intent": "Detect use of an allocated global pointer before it has been validated against null.",
    "trigger": "A global variable receives a dynamic allocation result and is later used without a prior null check on that global value.",
    "constraints": [
      "Global and local variables are treated the same by the rule.",
      "The check must apply to the allocated global variable itself, not a different alias unless the analyzer can prove equivalence.",
      "Report only once per violating global pointer variable."
    ],
    "csa_api_search_terms": [
      "VarDecl",
      "GlobalVar",
      "DeclRefExpr",
      "Region",
      "MemRegion",
      "SymbolicRegion",
      "LocationContext",
      "Store"
    ]
  },
  {
    "intent": "Detect use of a `calloc` result before a prior null check.",
    "trigger": "A pointer returned from `calloc` is used directly, or its first use occurs before any null guard on that pointer.",
    "constraints": [
      "`calloc` is covered the same as `malloc`.",
      "The rule is about prior validation, not the allocation call itself.",
      "If the value is never used, do not warn."
    ],
    "csa_api_search_terms": [
      "calloc",
      "CallExpr",
      "BuiltinFunction",
      "MallocChecker",
      "CallEvent",
      "ProgramState"
    ]
  },
  {
    "intent": "Detect use of a `realloc` result before a prior null check after reallocation.",
    "trigger": "A pointer is reassigned from `realloc`, then used before being checked for null on the new returned value.",
    "constraints": [
      "The pointer must be checked again after each `realloc` before any later use.",
      "A previous check on the old allocation does not satisfy the requirement for the new `realloc` result.",
      "If the reallocated pointer is never used afterward, do not report."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "SymbolReaper",
      "MemRegion",
      "SValBuilder",
      "assume",
      "assumeDual",
      "ProgramStateTrait"
    ]
  },
  {
    "intent": "Recognize acceptable null-check forms that satisfy the rule before first use.",
    "trigger": "A pointer from dynamic allocation is guarded by an equivalent null test before any use, including shorthand boolean forms.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)` as valid checks.",
      "The check must dominate the first use on the executed path.",
      "Do not warn when the pointer is allocated, checked, and then used only after the check passes."
    ],
    "csa_api_search_terms": [
      "ImplicitCastExpr",
      "UnaryOperator",
      "BinaryOperator",
      "NullPointerConstant",
      "BranchCondition",
      "ConditionTruthVal",
      "isNull"
    ]
  }
]