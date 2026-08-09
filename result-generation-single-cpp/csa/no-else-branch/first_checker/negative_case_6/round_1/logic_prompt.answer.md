[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted and therefore leaves uncovered conditions without an explicit else block.",
    "trigger": "An `if` statement has one or more `else if` branches, but the chain ends without a final `else` statement.",
    "constraints": [
      "Apply only to conditional chains that contain at least one `else if` branch.",
      "Flag structural absence of the final `else`, not the contents of any branch.",
      "Do not treat a standalone `if` or a simple `if-else` without `else if` as a violation.",
      "An empty final `else` is compliant if it is explicitly present.",
      "A final `else` containing only comments is still structurally compliant if the `else` block exists."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "getCond",
      "hasElseStorage",
      "CompoundStmt",
      "RecursiveASTVisitor",
      "Stmt::children",
      "clang::ast_matchers::ifStmt",
      "hasElse"
    ]
  },
  {
    "intent": "Identify the full shape of an if-else if chain so the checker can distinguish compliant chains from chains missing the terminal else.",
    "trigger": "Encountering an `IfStmt` node that may represent an `if`, `if-else`, or `if-else if-else` structure.",
    "constraints": [
      "Walk nested `IfStmt` nodes in the `else` branch to detect `else if` chains.",
      "Only chains with at least one nested `IfStmt` in the `else` position are in scope.",
      "The analysis should stop at the last nested `IfStmt` and verify that its `else` branch is present.",
      "Do not infer compliance from later statements after the chain; only the conditional structure matters."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "cast<IfStmt>",
      "dyn_cast<IfStmt>",
      "ASTContext",
      "Stmt",
      "RecursiveASTVisitor",
      "ParentMapContext",
      "clang::ast_matchers::ifStmt(hasElse(ifStmt()))"
    ]
  },
  {
    "intent": "Report a violation when a conditional chain with `else if` branches ends without an explicit final `else` clause.",
    "trigger": "The last `else if` in a chain has no `else` child statement.",
    "constraints": [
      "Emit one diagnostic per missing terminal `else` chain, not per nested `else if` node.",
      "The diagnostic should point at the chain or the final `else if`, whichever gives the clearest fix location.",
      "Do not require any specific statement inside the `else` branch beyond its existence.",
      "Avoid false positives on constructs where the `else` branch exists but is empty."
    ],
    "csa_api_search_terms": [
      "PathDiagnosticLocation",
      "CheckerContext",
      "BugReporter",
      "emitBasicReport",
      "IfStmt",
      "getElse",
      "SourceManager",
      "SourceLocation",
      "ExprEngine",
      "ProgramStateRef"
    ]
  },
  {
    "intent": "Distinguish compliant chains that include an explicit final `else` from non-compliant chains that substitute post-conditional statements for `else`.",
    "trigger": "A chain with one or more `else if` branches is followed by a normal statement instead of an `else` block.",
    "constraints": [
      "Treat statements after the chain as unrelated to satisfying the `else` requirement.",
      "Do not accept assignments, returns, comments, or any other code after the chain as a substitute for the missing `else`.",
      "Only an `else` attached to the conditional chain satisfies the rule."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "CompoundStmt",
      "Stmt::getBeginLoc",
      "Stmt::getEndLoc",
      "SourceRange",
      "clang::ast_matchers::stmt",
      "clang::ast_matchers::ifStmt"
    ]
  },
  {
    "intent": "Validate that the checker handles empty terminal `else` blocks as compliant, including those containing only comments in source.",
    "trigger": "A chain with `else if` branches ends with an explicit `else` whose body is empty or comment-only.",
    "constraints": [
      "Do not flag an empty `else` block.",
      "Do not require executable statements in the final `else`.",
      "Comments inside the `else` block are irrelevant to compliance, but the block itself must exist."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "CompoundStmt",
      "isEmpty",
      "getElse",
      "SourceManager",
      "Lexer",
      "RawCommentList",
      "clang::ast_matchers::compoundStmt"
    ]
  }
]