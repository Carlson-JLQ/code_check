[
  {
    "intent": "Detect use of a pointer returned by dynamic allocation before any null check on that allocation result.",
    "trigger": "A pointer assigned from `malloc`, `calloc`, or `realloc` is dereferenced, indexed, passed as an argument requiring a valid object, or otherwise used before an accepted null-check branch or condition has been evaluated for that same allocation result.",
    "constraints": [
      "Report only when the allocation result is actually used; unused allocated pointers are not violations.",
      "Accept explicit and implicit null checks such as `if (ptr != NULL)`, `if (ptr == NULL)`, `if (ptr)`, and `if (!ptr)` when they occur before first use.",
      "If the pointer is reassigned by `realloc`, require a new null check before any later use of the new value.",
      "Apply the rule to both local and global variables.",
      "Emit only one warning per violating pointer variable."
    ],
    "csa_api_search_terms": [
      "CallExpr malloc calloc realloc",
      "VarDecl init with allocator call",
      "BinaryOperator assignment to pointer variable",
      "ImplicitCastExpr to pointer",
      "IfStmt null check pointer",
      "UnaryOperator logical not pointer",
      "BranchCondition",
      "Dereference of symbol",
      "ArraySubscriptExpr on pointer",
      "RegionStore / LocationContext tracking"
    ]
  },
  {
    "intent": "Detect the specific violation where a dynamically allocated pointer is checked only after it has already been used.",
    "trigger": "A pointer from `malloc`, `calloc`, or `realloc` is used first and a null comparison or truthiness check appears only afterward in the same path or after the first use.",
    "constraints": [
      "The later check does not retroactively validate the earlier use.",
      "The warning should be tied to the first use that occurs before the check.",
      "Do not report if the pointer is never used after allocation.",
      "Do not report again for later uses of the same violating variable."
    ],
    "csa_api_search_terms": [
      "Post-dominating null check",
      "ExplodedGraph path-sensitive state",
      "SymbolRef comparison after use",
      "IfStmt after Deref",
      "CheckerContext",
      "ProgramState",
      "SVal / loc::MemRegionVal",
      "StmtPoint before branch"
    ]
  },
  {
    "intent": "Detect use of a global pointer allocated dynamically without a prior null check.",
    "trigger": "A global or file-scope pointer receives a result from `malloc`, `calloc`, or `realloc`, and a subsequent use occurs before any null check on that global variable.",
    "constraints": [
      "Global scope must be tracked the same way as local scope.",
      "A null check on a different alias or unrelated variable does not satisfy the requirement.",
      "If the global pointer is never used, do not report.",
      "Only one diagnostic per global pointer variable."
    ],
    "CSA_API search terms": [
      "GlobalVarDecl",
      "VarDecl with external storage",
      "CallExpr allocator assigned to global",
      "MemRegion global variable",
      "SymbolicRegion for global",
      "StoreManager global binding",
      "Use of global pointer before check"
    ]
  },
  {
    "intent": "Detect use of a pointer returned by `calloc` or `realloc` without a prior null check, including the post-reallocation case.",
    "trigger": "A pointer value coming directly from `calloc` or the new value returned by `realloc` is used before any accepted null check on that value.",
    "constraints": [
      "`calloc` is treated the same as other allocators.",
      "After `realloc`, the returned pointer must be checked again before any subsequent use, even if the original pointer was previously checked.",
      "If `realloc` is called and the resulting pointer is never used, do not report.",
      "One warning maximum per violating pointer variable."
    ],
    "CSA_API_search_terms": [
      "calloc CallExpr",
      "realloc CallExpr",
      "PostCall event",
      "SymbolReaper / symbol invalidation",
      "Newly returned pointer symbol",
      "Comparison with NULL after realloc",
      "Use-after-realloc without check"
    ]
  },
  {
    "intent": "Accept immediate and explicit null-check patterns that guard later pointer use.",
    "trigger": "A pointer from dynamic allocation is checked with an accepted null test before its first use, and the later use is dominated by the non-null branch or occurs only after an early return on the null branch.",
    "constraints": [
      "Allowed checks include `if (ptr != NULL)`, `if (ptr == NULL) return;`, `if (ptr)`, and `if (!ptr) return;`.",
      "The check must precede the first use in program order or control flow.",
      "The pointer may be used freely after the successful guard path.",
      "No warning should be emitted in these guarded cases."
    ],
    "CSA_API_search_terms": [
      "IfStmt",
      "BranchCondition pointer nonnull",
      "SymbolConjured / nonnull constraint",
      "AssumeDual / constraint manager",
      "ControlFlowCondition",
      "Null pointer comparison",
      "Early return guard"
    ]
  },
  {
    "intent": "Avoid false positives when an allocated pointer is never used, including after reassignment.",
    "trigger": "A pointer is assigned from an allocator but never dereferenced, indexed, passed, or otherwise used afterward, even if no null check is present.",
    "constraints": [
      "Pure allocation without use is not a violation.",
      "If the pointer is reassigned by `realloc` and still never used, do not report.",
      "Do not require a diagnostic for dead stores or unused allocations.",
      "This applies to both local and global variables."
    ],
    "CSA_API_search_terms": [
      "Unused value",
      "Dead store to pointer",
      "No dereference after allocation",
      "No post-call use",
      "Symbol not referenced later",
      "ExplodedGraph path with no use"
    ]
  }
]