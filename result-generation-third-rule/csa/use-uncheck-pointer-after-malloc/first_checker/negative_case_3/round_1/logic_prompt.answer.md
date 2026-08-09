I’m extracting the rule into structured detection units and keeping the output limited to JSON as requested.[
  {
    "intent": "Report a violation when a pointer returned by dynamic allocation is used before any null check, including the case where the check appears only after the first use.",
    "trigger": "A variable is assigned the result of `malloc`, `calloc`, or `realloc`, and a dereference, member access, array indexing, or other pointer use occurs before any dominating null check on that same variable.",
    "constraints": [
      "The null check must occur before the first use; a later check does not clear the violation.",
      "Accept explicit and implicit null checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "Do not report if the allocated pointer is never used.",
      "Only one warning should be emitted per violating pointer variable.",
      "Apply the rule to both local and global variables."
    ],
    "CSA_API_search_terms": [
      "MallocChecker",
      "RegionStore",
      "SVal",
      "SymbolRef",
      "ExprEngine",
      "check::Location",
      "check::Bind",
      "check::PreStmt<UnaryOperator>",
      "check::PreStmt<BinaryOperator>",
      "BugReporter",
      "ProgramState",
      "ConstraintManager"
    ]
  },
  {
    "intent": "Report a violation when a dynamically allocated pointer is used without any prior null check, even if the pointer was allocated immediately before use.",
    "trigger": "A pointer produced by `malloc`, `calloc`, or `realloc` is dereferenced or otherwise consumed without an intervening null guard on the control path from allocation to use.",
    "constraints": [
      "Allocation alone does not satisfy the rule.",
      "The first observable use must be dominated by a null check on the same variable.",
      "Checks on unrelated aliases or different variables do not satisfy the requirement unless they are proven to guard the same pointer value.",
      "A warning is still emitted even if allocation and use happen in the same function or statement block.",
      "Do not report multiple diagnostics for repeated uses of the same violating variable."
    ],
    "CSA_API_search_terms": [
      "CallEvent",
      "SValBuilder",
      "SymbolManager",
      "ProgramStateRef",
      "CheckerContext",
      "check::PostCall",
      "check::Location",
      "MemRegion",
      "SymbolicRegion",
      "Nullability"
    ]
  },
  {
    "intent": "Recognize acceptable pre-use null checks that make subsequent uses of an allocated pointer legal.",
    "trigger": "A pointer returned by `malloc`, `calloc`, or `realloc` is checked for null before its first use, and the use occurs only on the non-null path.",
    "constraints": [
      "Accept `if (ptr != NULL)`, `if (ptr)`, `if (ptr == nullptr)` in C++ mode, and `if (!ptr)` as valid gating checks.",
      "The safe use must be control-dependent on the check result.",
      "Do not flag code where the pointer is checked immediately after allocation and only used later on the proven non-null path.",
      "This applies equally to globals and locals."
    ],
    "CSA_API_search_terms": [
      "ConstraintManager",
      "assume",
      "assumeDual",
      "SVal::isZeroConstant",
      "NonLoc",
      "check::BranchCondition",
      "check::EndFunction",
      "ProgramStateTrait",
      "SymbolReaper"
    ]
  },
  {
    "intent": "Require a fresh null check after reallocation before any later use of the updated pointer value.",
    "trigger": "A pointer variable is assigned from `realloc`, and that variable is used before a new null check guarding the reallocated value.",
    "constraints": [
      "A prior check of the old value does not cover the result of `realloc`.",
      "The rule applies after every reallocation assignment.",
      "If the pointer is never used after the reallocation, do not report.",
      "Only one warning should be emitted for the variable even if multiple post-realloc uses are unsafe."
    ],
    "CSA_API_search_terms": [
      "realloc",
      "PostCall",
      "check::PostCall",
      "StoreManager",
      "BindingKey",
      "ProgramState",
      "SymbolRef",
      "InvalidateRegions",
      "check::Location"
    ]
  },
  {
    "intent": "Handle global dynamically allocated pointers with the same pre-use null-check requirement as local pointers.",
    "trigger": "A global pointer variable receives a result from `malloc`, `calloc`, or `realloc`, and a use occurs before any null check on that global.",
    "constraints": [
      "Global storage duration does not exempt the variable.",
      "Track initialization and use across function boundaries where the global is visible.",
      "Report when the global is used directly after allocation without a prior check.",
      "Do not report if the global is never used after allocation or reallocation."
    ],
    "CSA_API_search_terms": [
      "GlobalDecl",
      "VarRegion",
      "MemRegion",
      "ProgramState",
      "LiveVariables",
      "check::Location",
      "check::Bind",
      "check::PostStmt<BinaryOperator>",
      "SymbolRef"
    ]
  },
  {
    "intent": "Suppress diagnostics for allocated pointers that are never used, even though no null check was performed.",
    "trigger": "A pointer is returned by `malloc`, `calloc`, or `realloc`, but no dereference, access, or meaningful pointer use follows on any path.",
    "constraints": [
      "Allocation without use is not a violation.",
      "Assignments, escaping the pointer value, or storing it for later use are not necessarily direct uses unless the checker defines them as such.",
      "No warning should be emitted solely because the pointer lacks a null check."
    ],
    "CSA_API_search_terms": [
      "DeadSymbols",
      "SymbolReaper",
      "check::DeadSymbols",
      "ProgramState",
      "Store",
      "RegionStore",
      "SVal",
      "SymbolRef"
    ]
  }
]