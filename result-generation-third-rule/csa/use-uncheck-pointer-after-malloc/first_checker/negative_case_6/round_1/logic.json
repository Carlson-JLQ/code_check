[
  {
    "intent": "Detect a dynamically allocated pointer being used before any null check after `malloc`, `calloc`, or `realloc` returns it.",
    "trigger": "A pointer variable assigned from a dynamic allocation function is dereferenced, indexed, passed to a function, or otherwise used before any prior null comparison or truthiness check on that same allocation result.",
    "constraints": [
      "The check must happen before the first use of the allocated pointer.",
      "Accept explicit and implicit null checks such as `ptr != NULL`, `ptr == NULL`, `if (ptr)`, and `if (!ptr)`.",
      "If the pointer is never used after allocation, do not warn.",
      "If the pointer is reallocated with `realloc`, require a fresh null check before any later use.",
      "Apply the rule to both local and global variables.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "checkPostCall",
      "CallEvent",
      "RegionStore",
      "SVal",
      "ConstraintManager",
      "assume",
      "NullDereference",
      "checkLocation",
      "checkBind",
      "SymbolRef",
      "MemRegion",
      "VarRegion"
    ]
  },
  {
    "intent": "Detect direct use of a freshly allocated pointer without any preceding null validation.",
    "trigger": "Code performs an array access, field access, pointer dereference, or function call using a value originating from `malloc`/`calloc`/`realloc` before a null-check branch dominates that use.",
    "constraints": [
      "The use may appear immediately after allocation in the same block.",
      "The violation is based on ordering, not merely on the presence of a check somewhere later in the function.",
      "A later check does not repair an earlier use.",
      "The checker should treat `realloc` results the same as initial allocation results."
    ],
    "csa_api_search_terms": [
      "ExprEngine",
      "BugReporter",
      "ExplodedNode",
      "PostStmt",
      "PreStmt",
      "BinaryOperator",
      "UnaryOperator",
      "ArraySubscriptExpr",
      "CStyleCastExpr",
      "IgnoreParenImpCasts"
    ]
  },
  {
    "intent": "Detect null checks that occur only after the allocated pointer has already been used.",
    "trigger": "A pointer from dynamic allocation is used first, then later guarded by an `if` or equivalent null test, with the earlier use already violating the rule.",
    "constraints": [
      "The null check must precede the first use to be valid.",
      "Branching after the first use does not suppress the warning.",
      "Multiple later checks still do not repair the earlier violation.",
      "Only one warning should be emitted for the variable even if it is used multiple times before the first check."
    ],
    "csa_api_search_terms": [
      "ProgramState",
      "LocationContext",
      "ControlFlowCondition",
      "BranchNode",
      "IfStmt",
      "CheckerContext",
      "assumeDual",
      "DynamicTypeInfo"
    ]
  },
  {
    "intent": "Detect use of a dynamically allocated global variable before any null check.",
    "trigger": "A global pointer initialized or assigned from `malloc`, `calloc`, or `realloc` is later used without a prior null check on that same global value.",
    "constraints": [
      "The rule applies equally to globals and locals.",
      "Track assignments that happen in one function and uses that happen in another if the analysis path supports it.",
      "A null check must dominate the use for the relevant allocation instance.",
      "Only one warning per global variable violation."
    ],
    "csa_api_search_terms": [
      "GlobalVariable",
      "VarRegion",
      "MemRegion",
      "StoreManager",
      "DeclRefExpr",
      "RegionStoreManager",
      "bindLoc",
      "load"
    ]
  },
  {
    "intent": "Detect use of `calloc` results without a prior null check.",
    "trigger": "A pointer returned from `calloc` is used before being compared against null or tested in a truthiness condition.",
    "constraints": [
      "`calloc` must be treated as a dynamic allocation source equivalent to `malloc`.",
      "The first use after allocation must be dominated by a null check.",
      "If the pointer is never used, no diagnostic should be emitted.",
      "Do not emit duplicate warnings for repeated uses of the same unguarded allocation."
    ],
    "csa_api_search_terms": [
      "calloc",
      "MallocChecker",
      "CallDescription",
      "CallEvent",
      "PostCall",
      "AllocationState",
      "SymbolRef",
      "checkPostCall"
    ]
  },
  {
    "intent": "Detect use of `realloc` results without a fresh null check after reassignment.",
    "trigger": "A pointer reassigned from `realloc` is used before any new null check on the updated value.",
    "constraints": [
      "A previous check on the old value does not count for the new `realloc` result.",
      "The analysis must reset the checked status when `realloc` overwrites the pointer value.",
      "If the reallocated pointer is never used, do not warn.",
      "One warning per variable is enough even if multiple uses follow the missing check."
    ],
    "csa_api_search_terms": [
      "realloc",
      "checkPostCall",
      "SymbolReaper",
      "StoreManager",
      "RegionStore",
      "SymbolRef",
      "assume",
      "checkDeadSymbols"
    ]
  },
  {
    "intent": "Recognize valid null-check patterns that satisfy the rule before first use.",
    "trigger": "The allocated pointer is tested with direct comparison or implicit boolean check before any subsequent use, and the use occurs only on the checked path.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr == NULL)`, `if (ptr)`, and `if (!ptr)` forms.",
      "The check must be control-flow relevant to the use.",
      "Checks after use do not qualify.",
      "The rule is about presence and ordering of the check, not a specific syntax form."
    ],
    "csa_api_search_terms": [
      "BranchCondition",
      "ConditionTruthVal",
      "ImplicitCastExpr",
      "BinaryOperator",
      "UnaryOperator",
      "isNullPointerConstant",
      "assume",
      "ConstraintManager"
    ]
  },
  {
    "intent": "Suppress diagnostics when the allocated pointer is never used after allocation.",
    "trigger": "A pointer is returned by a dynamic allocation function and then remains unused for the rest of its lifetime in the analyzed scope.",
    "constraints": [
      "No warning should be emitted if there is no dereference, indexing, field access, call argument use, or similar consumption.",
      "The absence of a null check is not a violation by itself if there is no use.",
      "Track this behavior for both locals and globals."
    ],
    "csa_api_search_terms": [
      "LiveVariables",
      "DeadSymbols",
      "checkDeadSymbols",
      "SymbolRef",
      "ExplodedGraph",
      "ProgramState",
      "RegionStore"
    ]
  }
]