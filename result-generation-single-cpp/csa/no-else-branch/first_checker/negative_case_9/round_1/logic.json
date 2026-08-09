[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted, so every conditional chain with one or more else if branches must explicitly end with an else.",
    "trigger": "A conditional statement chain contains at least one `else if` branch and control reaches the end of the chain without an explicit final `else` block.",
    "constraints": [
      "Only flag chains that actually contain one or more `else if` branches.",
      "Do not flag a simple `if` statement with no `else if` branches.",
      "Treat an empty `else` block with a comment as compliant.",
      "The checker should validate structure, not the content of the else body.",
      "The final `else` must be explicitly present in source, even if it contains no executable statements."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "isIfStmt",
      "CompoundStmt",
      "hasElseStorage",
      "clang::IfStmt",
      "Stmt::children",
      "SourceManager"
    ]
  },
  {
    "intent": "Identify nested conditional chains formed by `if` followed by one or more `else if` clauses and confirm the chain terminates in an explicit else branch.",
    "trigger": "During AST traversal, an `IfStmt` is found whose `else` child is another `IfStmt`, and the terminal `IfStmt` in that chain has no `else` child.",
    "constraints": [
      "Traverse the full `else if` chain until the terminal `IfStmt` is reached.",
      "Report only when the terminal node lacks an `else` branch.",
      "Ignore unrelated nested `if` statements that are not part of an `else if` chain.",
      "Support chains of arbitrary length.",
      "Handle brace-wrapped and single-statement branches consistently."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "IfStmt::getCond",
      "IfStmt::getThen",
      "dyn_cast<IfStmt>",
      "isa<IfStmt>",
      "CFG",
      "RecursiveASTVisitor",
      "ASTContext",
      "SourceLocation"
    ]
  },
  {
    "intent": "Report a style/structural violation when an `if-else if` ladder falls through to following code instead of ending with an explicit `else` branch.",
    "trigger": "An `if` statement with one or more `else if` branches is followed by code after the chain, but the final chain node has no `else`, so the uncovered path is handled implicitly by later statements.",
    "constraints": [
      "The diagnostic should point to the top-level `if` or the terminal missing-else location in the chain.",
      "Do not infer semantic correctness from later `return`, `break`, or `throw` statements outside the chain.",
      "Do not require the else branch to contain logic beyond an explicit block or comment.",
      "Preserve compliance when the final else exists but is empty."
    ],
    "csa_api_search_terms": [
      "Stmt",
      "IfStmt",
      "CompoundStmt",
      "CFGBlock",
      "CFGElement",
      "ParentMapContext",
      "SourceRange",
      "DiagnosticsEngine"
    ]
  },
  {
    "intent": "Detect omission of an explicit final else in any conditional chain used to enumerate mutually exclusive conditions, regardless of the branch payload.",
    "trigger": "The analyzer observes an `if` followed by chained `else if` branches, and the last branch is not represented as an explicit `else` node in the AST/source.",
    "constraints": [
      "The rule applies even when branch bodies return, assign, or call functions.",
      "The rule applies even when the missing else would appear unreachable by inspection.",
      "The checker should not treat comments alone as equivalent to an else branch.",
      "An explicit empty else block with a comment is acceptable."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "CompoundStmt",
      "EmptyStmt",
      "Stmt::IgnoreParenImpCasts",
      "ASTMatchers",
      "clang::ast_matchers::ifStmt",
      "SourceManager",
      "Lexer"
    ]
  },
  {
    "intent": "Enforce explicit terminal else coverage for ladders built from `if` / `else if` constructs to prevent hidden uncovered cases.",
    "trigger": "A chain has multiple conditional alternatives and terminates without an `else` clause after the last `else if`.",
    "constraints": [
      "Flag only ladders containing one or more `else if` branches.",
      "A plain `if` with no `else if` branches is out of scope.",
      "The checker should accept an explicit `else {}` or `else { /* comment */ }`.",
      "The structural presence of `else` matters; semantic equivalence does not."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "isConstexpr",
      "ASTContext",
      "ParentMap",
      "SourceLocation",
      "SourceRange",
      "BugReporter"
    ]
  }
]