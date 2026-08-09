I’m extracting the detection units from the rule text and the negative example, then I’ll normalize them into a JSON array with the fields you asked for.[
  {
    "intent": "Detect use of a pointer returned by a dynamic allocation function before any null check is performed on that pointer.",
    "trigger": "A pointer assigned from `malloc`, `calloc`, or `realloc` is dereferenced or otherwise used before a preceding null-check branch or condition proves it non-null.",
    "constraints": [
      "The null check must occur before the first use; a check after use is a violation.",
      "Accept explicit and implicit null checks, including `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not report.",
      "If a pointer is reallocated, require a new null check before any subsequent use after the `realloc` assignment.",
      "Apply the rule to both local and global variables.",
      "Report only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "MallocChecker",
      "CallEvent",
      "SVal",
      "SymbolRef",
      "ProgramState",
      "ExprEngine",
      "checkPostCall",
      "checkLocation",
      "checkBind",
      "dyn_cast<CallExpr>",
      "isNull",
      "Assume",
      "RegionState"
    ]
  },
  {
    "intent": "Detect a global pointer allocated with dynamic memory and then used without a prior null check.",
    "trigger": "A global variable receives the result of `malloc`/`calloc`/`realloc` and is dereferenced or otherwise used before any null check.",
    "constraints": [
      "Global variables are treated the same as local variables.",
      "A later null check does not satisfy the rule if the global was already used.",
      "One report only for the global pointer variable even if multiple uses occur before checking."
    ],
    "csa_api_search_terms": [
      "GlobalVariable",
      "VarDecl",
      "DeclRefExpr",
      "UnaryOperator",
      "BinaryOperator",
      "checkLocation",
      "checkPostStmt<BinaryOperator>",
      "SVal",
      "SymbolRef",
      "ProgramState"
    ]
  },
  {
    "intent": "Detect use after `calloc` without a prior null check.",
    "trigger": "A pointer returned by `calloc` is used before any null-check condition establishes it is non-null.",
    "constraints": [
      "`calloc` is covered the same as other dynamic allocation functions.",
      "Explicit, implicit, and shorthand null checks are acceptable only if they occur before first use.",
      "If unused after allocation, no warning."
    ],
    "csa_api_search_terms": [
      "calloc",
      "CallExpr",
      "CallEvent",
      "MallocChecker",
      "checkPostCall",
      "SVal",
      "SymbolRef",
      "ProgramState"
    ]
  },
  {
    "intent": "Detect use after `realloc` without a fresh prior null check.",
    "trigger": "A pointer is reassigned from `realloc` and then used before a new null check on the reallocated result.",
    "constraints": [
      "A previously checked pointer must be checked again after `realloc` because the result may change.",
      "The check must happen before any subsequent use of the reallocated value.",
      "If the reallocated pointer is never used, do not report.",
      "Only one warning should be emitted for the pointer variable."
    ],
    "csa_api_search_terms": [
      "realloc",
      "CallExpr",
      "CallEvent",
      "MallocChecker",
      "checkPostCall",
      "checkLocation",
      "SymbolRef",
      "ProgramState",
      "SVal"
    ]
  },
  {
    "intent": "Allow correct patterns where the allocation is immediately checked before use.",
    "trigger": "A pointer returned by `malloc`, `calloc`, or `realloc` is checked for null before any dereference or other use, and usage occurs only on the non-null path.",
    "constraints": [
      "Recognize `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)` as valid null-check forms.",
      "Do not report when the pointer is never used after allocation.",
      "Do not report when the pointer is only used inside the branch that confirms it is non-null."
    ],
    "csa_api_search_terms": [
      "BranchCondition",
      "ImplicitCastExpr",
      "BinaryOperator",
      "UnaryOperator",
      "NullPointerConstant",
      "Assume",
      "ProgramState",
      "SVal"
    ]
  }
]