[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any null check on that specific allocation result.",
    "trigger": "A value from `malloc`, `calloc`, or `realloc` is assigned to a pointer variable and that pointer is dereferenced, indexed, passed as a non-null-required argument, or otherwise used before an explicit or implicit null check on the same allocation result.",
    "constraints": [
      "The null check must occur before the first use of the allocated pointer.",
      "Accept explicit comparisons such as `ptr != NULL` and `ptr == NULL`.",
      "Accept implicit checks such as `if (ptr)` and `if (!ptr)`.",
      "If the pointer is never used, do not report a violation.",
      "If the pointer is reallocated, require a new null check before any later use of the new allocation result.",
      "Apply the rule to both local and global variables.",
      "Report at most one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "malloc",
      "calloc",
      "realloc",
      "DynTypedNode",
      "Expr",
      "Stmt",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "DeclRefExpr",
      "VarDecl",
      "GlobalVarDecl",
      "SVal",
      "SymbolRef",
      "ProgramState",
      "CheckerContext",
      "ExplodedNode",
      "BugReport",
      "bugreporter",
      "registerPreStmt",
      "registerPostStmt",
      "check::PreStmt<BinaryOperator>",
      "check::PreStmt<UnaryOperator>",
      "check::PostStmt<CallExpr>",
      "MemRegion",
      "SymbolManager"
    ]
  },
  {
    "intent": "Detect direct use of a freshly allocated pointer without any preceding null check.",
    "trigger": "A pointer assigned from `malloc` is immediately dereferenced or otherwise consumed in a way that assumes validity, with no earlier null comparison or guard on that pointer.",
    "constraints": [
      "The allocation-to-use path must be tracked within the same control flow.",
      "A later null check does not satisfy the rule if the pointer has already been used.",
      "Handle both local and global storage for the allocated pointer.",
      "One report per pointer variable even if multiple unsafe uses occur."
    ],
    "csa_api_search_terms": [
      "CallExpr",
      "malloc",
      "CXXMemberCallExpr",
      "UnaryOperator",
      "BO_Deref",
      "BinaryOperator",
      "IfStmt",
      "BranchCondition",
      "DeclRefExpr",
      "VarDecl",
      "ProgramState",
      "ConstraintManager",
      "SVal",
      "loc::MemRegionVal",
      "BugType"
    ]
  },
  {
    "intent": "Detect null checks that happen only after an unsafe use of the allocated pointer.",
    "trigger": "A pointer from dynamic allocation is used first, and only later a null-check expression appears for that same pointer.",
    "constraints": [
      "The check must precede first use to be considered valid.",
      "Post-use checks do not retroactively clear the violation.",
      "The warning should still be associated with the variable that was used before being checked.",
      "Do not emit multiple warnings for repeated post-use checks on the same variable."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "NullPointerConstant",
      "Expr",
      "CallExpr",
      "malloc",
      "calloc",
      "realloc",
      "DeclRefExpr",
      "VarDecl",
      "CFG",
      "ControlFlowContext",
      "ProgramState",
      "CheckerContext"
    ]
  },
  {
    "intent": "Detect unsafe use of pointers returned by `calloc` without a prior null check.",
    "trigger": "A pointer returned by `calloc` is used before any valid null check on that allocation result.",
    "constraints": [
      "`calloc` results are treated the same as `malloc` results.",
      "The first use after allocation must be dominated by a null check on the same pointer.",
      "No warning if the pointer is allocated and never used.",
      "Only one warning per variable."
    ],
    "csa_api_search_terms": [
      "calloc",
      "CallExpr",
      "DeclRefExpr",
      "VarDecl",
      "BinaryOperator",
      "UnaryOperator",
      "IfStmt",
      "ProgramState",
      "SVal",
      "MemRegion",
      "BugReport"
    ]
  },
  {
    "intent": "Detect unsafe use of pointers returned by `realloc` without a new null check after reallocation.",
    "trigger": "A pointer is reassigned from `realloc`, and the new value is used before being checked for null.",
    "constraints": [
      "A prior check on an earlier allocation result does not satisfy the requirement after `realloc`.",
      "The reallocated pointer must be checked again before any subsequent use.",
      "If the reallocated pointer is never used, do not report.",
      "Track reassignment on both local and global variables.",
      "One warning per violating variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "BinaryOperator",
      "DeclRefExpr",
      "VarDecl",
      "GlobalVarDecl",
      "UnaryOperator",
      "IfStmt",
      "ProgramState",
      "SymbolRef",
      "SVal",
      "CheckerContext"
    ]
  },
  {
    "intent": "Detect unsafe use of a globally stored dynamically allocated pointer without a prior null check.",
    "trigger": "A global variable receives a pointer from dynamic allocation and is used before any null check on that variable.",
    "constraints": [
      "Global variables are in scope for the rule exactly like local variables.",
      "The checker must handle uses that occur in different functions from the allocation site.",
      "A later check in another function does not prevent the violation if the use already occurred.",
      "Only one diagnostic should be issued for the global variable."
    ],
    "csa_api_search_terms": [
      "GlobalVarDecl",
      "VarDecl",
      "CallExpr",
      "malloc",
      "calloc",
      "realloc",
      "DeclRefExpr",
      "BinaryOperator",
      "UnaryOperator",
      "ProgramState",
      "SymbolRef",
      "MemRegion",
      "BugReport",
      "AnalysisManager"
    ]
  },
  {
    "intent": "Allow safe code where the dynamic allocation result is checked immediately before use.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is tested with a null check before its first use, and the use occurs only on the checked non-null path.",
    "constraints": [
      "Recognize explicit and implicit null checks.",
      "Accept `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)` style guards as valid checks when they control the use path appropriately.",
      "Do not report if the pointer is never used.",
      "Do not report if a `realloc` result is rechecked before later use."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "BinaryOperator",
      "UnaryOperator",
      "ImplicitCastExpr",
      "DeclRefExpr",
      "CallExpr",
      "malloc",
      "calloc",
      "realloc",
      "ProgramState",
      "ConstraintManager",
      "SVal",
      "BranchCondition"
    ]
  },
  {
    "intent": "Ensure only one warning is emitted for each violating pointer variable even if there are multiple unsafe uses.",
    "trigger": "A single pointer variable from dynamic allocation is used multiple times without a prior check, or is checked only after one or more unsafe uses.",
    "constraints": [
      "Deduplicate diagnostics by variable identity, not by individual use site.",
      "Multiple dereferences of the same unchecked pointer should still yield one warning.",
      "Reallocation of the same variable can start a new checked/unchecked lifecycle, but each violating lifecycle still produces at most one warning."
    ],
    "csa_api_search_terms": [
      "BugType",
      "BugReport",
      "PathDiagnosticLocation",
      "VarDecl",
      "DeclRefExpr",
      "SymbolRef",
      "ProgramState",
      "ExplodedNode",
      "CheckerContext",
      "SourceManager"
    ]
  }
]