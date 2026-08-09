[
  {
    "intent": "Detect if-else if chains that omit a final else branch, because any chain with one or more else if branches must end with an explicit else.",
    "trigger": "An `if` statement whose `else` arm contains another `if` statement, repeated for one or more `else if` levels, where the outermost chain has no terminal `else` statement.",
    "constraints": [
      "Only apply when the conditional chain contains at least one `else if` branch.",
      "Flag missing final `else` regardless of whether the omitted branch would have been empty or non-empty.",
      "Do not require inspection of the contents of the `else` branch; the rule is structural.",
      "Do not flag a simple `if` without any `else if` branches.",
      "Do not flag chains that already include an explicit final `else`, including empty `else` blocks with comments."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "CompoundStmt",
      "getElse()->getStmtClass",
      "ignoringParenImpCasts",
      "else if chain",
      "AST matcher IfStmt hasElse",
      "clang::IfStmt"
    ]
  },
  {
    "intent": "Verify the final branch of a conditional chain is explicitly present rather than simulated by later statements after the chain.",
    "trigger": "A sequence of `if` / `else if` statements followed by standalone statements that appear to act as a fallback path instead of a terminal `else` block.",
    "constraints": [
      "Treat statements after the conditional chain as non-compliant when they are used in place of the required final `else`.",
      "The checker should look for structural omission, not semantic equivalence.",
      "A comment alone after the chain does not satisfy the `else` requirement.",
      "An empty `else {}` or `else { /* comment */ }` is compliant.",
      "Focus on the outermost chain so nested unrelated `if` statements are not confused with `else if` branches."
    ],
    "csa_api_search_terms": [
      "Stmt::children",
      "IfStmt::getElse",
      "CompoundStmt::body_begin",
      "ASTContext",
      "Stmt::getLocEnd",
      "SourceManager",
      "CFGElement",
      "AST matcher hasDescendant(IfStmt)"
    ]
  },
  {
    "intent": "Identify complete `if-else if-else` chains and distinguish them from incomplete chains for diagnostic suppression.",
    "trigger": "An `if` statement with one or more `else if` branches that also has a terminal `else` branch, including an empty block or comment-only branch.",
    "constraints": [
      "Do not report compliant chains with an explicit final `else`.",
      "The checker may need to descend through nested `IfStmt` nodes to determine whether the chain terminates in an `else`.",
      "Preserve compatibility with formatting and brace style variations.",
      "Comments inside an empty `else` block are acceptable evidence of explicit inclusion.",
      "The final `else` may contain any statements, including no-ops."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "IfStmt::getThen",
      "isa<IfStmt>",
      "dyn_cast<IfStmt>",
      "AST matcher ifStmt(hasElse(stmt()))",
      "Stmt::IgnoreImplicit",
      "clang::RecursiveASTVisitor"
    ]
  }
]