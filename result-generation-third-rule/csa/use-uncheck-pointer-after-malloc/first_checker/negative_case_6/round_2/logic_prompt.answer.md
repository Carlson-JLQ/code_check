I’m extracting the rule into detector-sized units and keeping the output strictly JSON. I’m treating the negative test as evidence for the warning shape and de-duplicating by pointer variable.[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any prior null-check on that allocation result.",
    "trigger": "A local or global pointer receives the result of `malloc`, `calloc`, or `realloc`, and that pointer is dereferenced or otherwise used before a null check dominates the first use.",
    "constraints": [
      "The check must occur before the first use; a later check does not suppress the violation.",
      "Accept explicit and implicit null checks, including `ptr != NULL`, `ptr == NULL`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not report.",
      "If the pointer is reallocated with `realloc`, require a fresh null check before any later use.",
      "Apply the rule equally to local and global variables.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "BinaryOperator null compare",
      "UnaryOperator !ptr",
      "ImplicitCastExpr to boolean",
      "DeclRefExpr pointer use",
      "ArraySubscriptExpr",
      "UnaryOperator *ptr",
      "Store/Load of allocated pointer",
      "SymbolRefExpr",
      "checkPostCall",
      "checkLocation",
      "checkBind"
    ]
  },
  {
    "intent": "Detect immediate use of a freshly allocated pointer without an intervening null guard.",
    "trigger": "Code assigns an allocation result to a pointer and then uses it directly, such as `pa[0] = ...`, `*p = ...`, or passing it to a function requiring a valid non-null object, without any preceding branch or condition proving non-null.",
    "constraints": [
      "The allocation source may be any supported allocator function.",
      "The violation is tied to the first unchecked use after allocation.",
      "A later `if (ptr)` or `if (!ptr)` does not repair the earlier use.",
      "Do not emit a second warning for later uses of the same pointer variable."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "CallEvent",
      "PostCall",
      "SVal",
      "RegionStore",
      "ExplodedGraph",
      "ProgramState",
      "SymbolReaper",
      "ArraySubscriptExpr",
      "UnaryOperator dereference",
      "call to malloc-like function"
    ]
  },
  {
    "intent": "Detect use-after-allocation on a global pointer that was assigned from dynamic memory without a prior null check.",
    "trigger": "A global variable is assigned the result of `malloc`, `calloc`, or `realloc`, and later used before any null test on that variable.",
    "constraints": [
      "Global storage does not change the rule: the first use still requires a preceding null check.",
      "Track assignments and uses across function boundaries when feasible within CSA path-sensitive analysis.",
      "Reassignment via `realloc` must restart the check requirement for the new value.",
      "Only one diagnostic per global pointer variable."
    ],
    "csa_api_search_terms": [
      "GlobalVariable",
      "VarRegion",
      "MemRegion",
      "SymbolicRegion",
      "StoreManager",
      "checkBeginFunction",
      "checkEndFunction",
      "checkBind",
      "checkLocation",
      "malloc-like global pointer"
    ]
  },
  {
    "intent": "Detect missing revalidation after `realloc` before subsequent pointer use.",
    "trigger": "A pointer previously allocated or previously checked is passed to `realloc`, and the returned value is used without a new null check before the next dereference or equivalent use.",
    "constraints": [
      "`realloc` creates a new allocation result that must be checked again.",
      "A check performed only for the old pointer value is insufficient.",
      "If the reallocated pointer is never used, do not report.",
      "One warning only, even if the pointer is used multiple times after the missed check."
    ],
    "csa_api_search_terms": [
      "realloc",
      "malloc-like call",
      "post-call return value",
      "null dereference after realloc",
      "ProgramState",
      "SymbolReaper",
      "checkPostCall",
      "checkPreStmt",
      "checkLocation"
    ]
  },
  {
    "intent": "Suppress reporting when the allocation result is proven non-null before first use.",
    "trigger": "The pointer returned by allocation is guarded by a dominating null check before any use, including shorthand checks such as `if (ptr)` or `if (!ptr) return;`.",
    "constraints": [
      "The check must be reachable on all paths leading to the use.",
      "Treat explicit and implicit boolean tests as valid null checks.",
      "Do not warn when the pointer is allocated and never used.",
      "Do not warn when use occurs only after a check has established non-nullness."
    ],
    "csa_api_search_terms": [
      "ConstraintManager",
      "assume",
      "assumeDual",
      "TruthVal",
      "ConditionBRVisitor",
      "BranchCondition",
      "BinaryOperator",
      "UnaryOperator !",
      "NonNull assumption"
    ]
  }
]