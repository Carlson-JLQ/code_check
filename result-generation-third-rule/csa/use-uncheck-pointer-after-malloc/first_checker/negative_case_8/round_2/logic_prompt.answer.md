I’m extracting the detection units directly from the rule text and the negative example, then I’ll format them as strict JSON only.[
  {
    "intent": "Detect use of a pointer returned by dynamic memory allocation before any prior non-null check.",
    "trigger": "A pointer from malloc, calloc, or realloc is dereferenced, read, written, passed as an argument, or otherwise used before an earlier null check on that pointer dominates the use.",
    "constraints": [
      "Report only when the first use occurs before the first valid null check.",
      "Accept explicit and implicit null checks, including ptr != NULL, ptr == NULL, if (ptr), and if (!ptr).",
      "If the allocated pointer is never used, do not report.",
      "If the pointer is reallocated, require a new null check before any later use.",
      "Apply to both local and global variables.",
      "Emit only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "DynTypedNode",
      "DeclRefExpr",
      "ImplicitCastExpr",
      "UnaryOperator",
      "BinaryOperator",
      "ExprEngine",
      "SVal",
      "ProgramState",
      "check::Location",
      "check::PreStmt",
      "check::PostStmt",
      "BugReporter"
    ]
  },
  {
    "intent": "Detect violation when a dynamically allocated pointer is checked for null only after it has already been used.",
    "trigger": "A pointer obtained from malloc, calloc, or realloc is used first and a null comparison occurs only later in the same execution path.",
    "constraints": [
      "The check must precede the first use to satisfy the rule.",
      "Late checks do not suppress the warning.",
      "Accept shorthand and explicit null checks equally.",
      "Report once per variable even if multiple later checks occur."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "BranchCondition",
      "ProgramState",
      "ConstraintManager",
      "BugReporter"
    ]
  },
  {
    "intent": "Detect use of a global pointer initialized by dynamic allocation without a prior null check.",
    "trigger": "A global variable assigned the result of malloc, calloc, or realloc is accessed before any null check on that global.",
    "constraints": [
      "Scope does not matter; global variables are included.",
      "The first use must be guarded by a prior null check.",
      "Do not report if the global pointer is never used.",
      "Emit one warning per global pointer variable."
    ],
    "csa_api_search_terms": [
      "VarDecl",
      "GlobalVar",
      "malloc",
      "calloc",
      "realloc",
      "DeclRefExpr",
      "Load",
      "Store",
      "ProgramState",
      "BugReporter"
    ]
  },
  {
    "intent": "Detect use of a reallocated pointer without a fresh null check after the reallocation.",
    "trigger": "A pointer passed to realloc is used after realloc returns, but no null check is performed on the returned pointer before that use.",
    "constraints": [
      "Reallocation resets the requirement for a null check.",
      "The post-realloc check must occur before any subsequent use.",
      "If the pointer is not used after realloc, do not report.",
      "Apply the one-warning-per-variable rule across repeated reallocations."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "ReturnValue",
      "ProgramState",
      "SVal",
      "SymbolRef",
      "BinaryOperator",
      "UnaryOperator",
      "BugReporter"
    ]
  },
  {
    "intent": "Detect direct dereference of a dynamically allocated struct member pointer before a null check.",
    "trigger": "A member like c.data_ptr receives malloc/calloc/realloc result and is dereferenced or otherwise used before a prior null check on that member.",
    "constraints": [
      "Struct member pointers are in scope for this rule.",
      "The check must apply to the same member expression or tracked storage location.",
      "Accept both explicit comparisons and implicit truthiness checks.",
      "Do not report if the member is assigned but never used."
    ],
    "csa_api_search_terms": [
      "FieldDecl",
      "MemberExpr",
      "CXXThisExpr",
      "DeclRefExpr",
      "malloc",
      "calloc",
      "realloc",
      "UnaryOperator",
      "BinaryOperator",
      "BugReporter"
    ]
  }
]