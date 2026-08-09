I’m extracting the detection units directly from the rule text and the negative example, and I’m keeping them aligned to CSA-relevant patterns rather than inventing new semantics.[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any null check has established it is non-null.",
    "trigger": "A variable assigned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed as an argument that implies dereference, or otherwise used before an earlier null-check guard is present on that execution path.",
    "constraints": [
      "The null check must occur before the first use; a check after use still violates the rule.",
      "Accept explicit and implicit checks such as `if (ptr != NULL)`, `if (ptr)`, and `if (!ptr)`.",
      "If the allocated pointer is never used, do not warn.",
      "Report only one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "malloc",
      "calloc",
      "realloc",
      "PointerDereference",
      "ArraySubscriptExpr",
      "UnaryOperator *",
      "BinaryOperator != NULL",
      "BranchCondition",
      "VarDecl",
      "ImplicitCastExpr"
    ]
  },
  {
    "intent": "Detect null-checks that happen only after the dynamic pointer has already been used.",
    "trigger": "A pointer from dynamic allocation is first used, and only later appears in a null comparison or guard statement.",
    "constraints": [
      "A post-use null check does not satisfy the rule.",
      "The warning is tied to the first unsafe use, not the later check.",
      "Do not emit duplicate warnings for the same pointer variable."
    ],
    "CSA API search terms": [
      "malloc",
      "calloc",
      "realloc",
      "StmtNode",
      "BranchCondition",
      "CFG",
      "path-sensitive",
      "PointerDereference",
      "BinaryOperator"
    ]
  },
  {
    "intent": "Detect uses of dynamically allocated local pointers that are never checked for non-null anywhere before first use.",
    "trigger": "A local variable receives the result of an allocation function and is then used without any reachable prior null check.",
    "constraints": [
      "Local scope only for this unit, but the rule semantics are identical to globals.",
      "Do not report if the variable is allocated but never used.",
      "Any accepted null-check form before use suppresses the warning."
    ],
    "CSA API search terms": [
      "VarDecl",
      "LocalVarDecl",
      "malloc",
      "calloc",
      "realloc",
      "DereferencedDeclRef",
      "ExplodedGraph",
      "PostStmt",
      "BranchCondition"
    ]
  },
  {
    "intent": "Detect uses of dynamically allocated global pointers that are never checked for non-null before use.",
    "trigger": "A global variable is assigned from an allocation function and then read, written, dereferenced, indexed, or otherwise used without a prior null check.",
    "constraints": [
      "The rule applies equally to global and local variables.",
      "A global pointer may be assigned in one function and used in another; the check must still precede the first use on the path.",
      "Only one warning per violating pointer variable."
    ],
    "CSA API search terms": [
      "GlobalVarDecl",
      "malloc",
      "calloc",
      "realloc",
      "RegionStore",
      "SymbolRef",
      "PointerDereference",
      "ArraySubscriptExpr",
      "LiveVariables"
    ]
  },
  {
    "intent": "Detect pointers returned by `calloc` that are used before a prior null check.",
    "trigger": "A pointer assigned from `calloc` is used directly without an earlier null comparison or branch on its value.",
    "constraints": [
      "`calloc` is treated the same as other dynamic allocation sources.",
      "The check must be before the first use.",
      "Never-used pointers are exempt."
    ],
    "CSA API search terms": [
      "calloc",
      "CallExpr",
      "PointerDereference",
      "ArraySubscriptExpr",
      "BranchCondition",
      "SymbolRef"
    ]
  },
  {
    "intent": "Detect pointers returned by `realloc` that are used after reassignment without being checked again.",
    "trigger": "A pointer previously allocated or already checked is reassigned from `realloc` and then used without a fresh null check after the `realloc` call.",
    "constraints": [
      "A successful earlier check on the old value does not satisfy the post-`realloc` requirement.",
      "The pointer must be checked again before any subsequent use after reallocation.",
      "If the pointer is not used after `realloc`, do not warn."
    ],
    "CSA API search terms": [
      "realloc",
      "CallExpr",
      "VarDecl",
      "SymbolRef",
      "PointerDereference",
      "BinaryOperator != NULL",
      "BranchCondition",
      "PostStmt"
    ]
  },
  {
    "intent": "Detect unsafe direct use of a dynamically allocated pointer in the same statement that receives the allocation result, when no prior guard exists.",
    "trigger": "An allocation assignment is immediately followed by a use of the same pointer before any intervening null-check branch.",
    "constraints": [
      "The allocation expression and the use may appear in adjacent statements or within the same block.",
      "Shorthand checks like `if (ptr)` or `if (!ptr)` are valid only if they occur before the use.",
      "Do not warn on allocation-only statements."
    ],
    "CSA API search terms": [
      "malloc",
      "calloc",
      "realloc",
      "StmtSequence",
      "CFGBlock",
      "PointerDereference",
      "ImplicitCastExpr",
      "BranchCondition"
    ]
  },
  {
    "intent": "Detect any first-use violation for dynamically allocated pointers regardless of storage duration or aliasing context.",
    "trigger": "A pointer originating from allocation is accessed through an alias, member, array, or direct variable use before a null check has guarded that value.",
    "constraints": [
      "The rule cares about the allocated pointer value, not just the original variable name.",
      "Apply equally to locals and globals.",
      "Report only one warning per violating pointer variable, even if multiple uses exist."
    ],
    "CSA API search terms": [
      "SymbolRef",
      "SVal",
      "RegionStore",
      "MemRegion",
      "PointerDereference",
      "ArraySubscriptExpr",
      "FieldDecl",
      "GlobalVarDecl",
      "VarDecl"
    ]
  }
]