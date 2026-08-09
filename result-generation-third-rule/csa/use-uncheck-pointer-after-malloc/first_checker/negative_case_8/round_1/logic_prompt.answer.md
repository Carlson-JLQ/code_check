I’m extracting the checker logic into a structured JSON list, including the negative example as a detection unit and keeping the fields you asked for: intent, trigger, constraints, and CSA API search terms.[
  {
    "intent": "Report use of a dynamically allocated pointer before any null check has established it is non-null.",
    "trigger": "A pointer returned by `malloc`, `calloc`, `realloc`, or an equivalent dynamic allocation function is dereferenced, passed to a use site, or otherwise consumed before any preceding null check on that pointer in the current allocation epoch.",
    "constraints": [
      "The null check must occur before the first use; a check after the first use is still a violation.",
      "Accept explicit and implicit null checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the pointer is never used after allocation, do not report.",
      "Apply the same rule to local, global, and struct-member pointer variables.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "CallEvent",
      "ProgramState",
      "SymbolRef",
      "SVal",
      "ConstraintManager",
      "check::PostCall",
      "check::PreStmt<BinaryOperator>",
      "check::BranchCondition",
      "check::Location",
      "isNullPointer",
      "assume",
      "DynamicExtent",
      "RegionStore"
    ]
  },
  {
    "intent": "Detect direct use of a freshly allocated pointer without any prior null guard.",
    "trigger": "A value from `malloc` or `calloc` flows into a variable and that variable is dereferenced or otherwise used before a dominating null test.",
    "constraints": [
      "The initial allocation site alone is not sufficient as a safety check.",
      "Follow aliases and struct members when tracking the allocated pointer value.",
      "Do not report if the pointer is never read, dereferenced, or passed into a consuming call.",
      "Ignore checks that occur only after the first consuming use."
    ],
    "csa_api_search_terms": [
      "AllocationFamily",
      "malloc",
      "calloc",
      "MemRegion",
      "FieldRegion",
      "Load",
      "Store",
      "UnaryOperator",
      "BinaryOperator"
    ]
  },
  {
    "intent": "Detect late null checking, where the pointer is checked only after it has already been used.",
    "trigger": "A dynamically allocated pointer is used first and only later compared against null in a branch or condition.",
    "constraints": [
      "The rule is violated even if a later null check exists.",
      "The later check does not retroactively validate the earlier use.",
      "One report per pointer variable, even if multiple late checks occur."
    ],
    "csa_api_search_terms": [
      "CFGBlock",
      "BranchCondition",
      "PreStmt",
      "PostStmt",
      "SymbolReaper",
      "ExplodedNode",
      "ProgramState"
    ]
  },
  {
    "intent": "Detect use of a global dynamically allocated pointer without a prior null check.",
    "trigger": "A global pointer assigned from dynamic allocation is accessed in a function before any null check on that global pointer along the executed path.",
    "constraints": [
      "The rule applies equally to global and local variables.",
      "Track interprocedural visibility when the global is allocated in one place and used in another.",
      "Do not suppress the report because the allocation and use happen in different functions."
    ],
    "csa_api_search_terms": [
      "VarRegion",
      "GlobalVarRegion",
      "DeclRefExpr",
      "StoreManager",
      "CallEvent",
      "ProgramState",
      "LocationContext"
    ]
  },
  {
    "intent": "Detect unguarded use of pointers returned by `realloc` after reassignment.",
    "trigger": "A pointer is updated by `realloc` and then used before a new null check has been performed for that reallocated value.",
    "constraints": [
      "A pointer must be checked again after reallocation before any subsequent use.",
      "Treat the post-realloc value as a new allocation epoch for null-check tracking.",
      "If the reallocated pointer is never used, do not report.",
      "Do not reuse an earlier check performed before the `realloc` call as proof for the new value."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallEvent",
      "SVal",
      "SymbolRef",
      "ProgramState",
      "check::PostCall",
      "check::PreCall",
      "RegionStore"
    ]
  },
  {
    "intent": "Model acceptable null-check forms that should prevent a warning when they dominate first use.",
    "trigger": "A dynamic allocation result is guarded by any standard null comparison or implicit boolean test before first use.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr == NULL)`, `if (ptr)`, and `if (!ptr)` as valid checks.",
      "The check must be control-flow relevant to the later use.",
      "The use must occur only on the path where the pointer is known non-null."
    ],
    "csa_api_search_terms": [
      "BranchCondition",
      "ConstraintManager",
      "Assume",
      "BinaryOperator",
      "UnaryOperator",
      "NonNull",
      "isZeroConstant"
    ]
  },
  {
    "intent": "Suppress reports when the allocated pointer is never actually used.",
    "trigger": "A pointer is obtained from dynamic allocation and then never dereferenced, read, passed as a consuming argument, or otherwise used.",
    "constraints": [
      "Allocation alone is not a violation.",
      "No warning should be emitted if there is no first use to validate.",
      "This applies even if no null check is present."
    ],
    "csa_api_search_terms": [
      "DeadSymbols",
      "SymbolReaper",
      "LiveVariables",
      "PostStmt",
      "Store",
      "Load"
    ]
  },
  {
    "intent": "Cover struct-member pointers initialized from allocation and then used without a check.",
    "trigger": "A field such as `c.data_ptr` receives a dynamically allocated pointer and is then dereferenced before any null check on that field value.",
    "constraints": [
      "Struct members are in scope for the rule.",
      "The null-check requirement follows the stored pointer value, not just the variable name.",
      "Report the member use even if the allocation was assigned through a field expression."
    ],
    "csa_api_search_terms": [
      "FieldRegion",
      "MemberExpr",
      "StoreManager",
      "Load",
      "DeclRefExpr",
      "RegionStore",
      "SVal"
    ]
  },
  {
    "intent": "Encode the negative example where a struct member allocated by `malloc` is dereferenced immediately.",
    "trigger": "In `negative_struct_member.c`, `c.data_ptr = (int*)malloc(sizeof(int));` is followed by `*(c.data_ptr) = 42;` without any preceding null check.",
    "constraints": [
      "Emit the warning at the dereference line.",
      "Use the message: `禁止动态分配的指针变量未检查即使用 [gjb8114-r-1-3-8]`.",
      "Do not require a second warning for the same pointer variable later in the function."
    ],
    "csa_api_search_terms": [
      "malloc",
      "FieldRegion",
      "UnaryOperator",
      "check::PreStmt<UnaryOperator>",
      "BugReporter",
      "PathSensitiveBugReport"
    ]
  }
]