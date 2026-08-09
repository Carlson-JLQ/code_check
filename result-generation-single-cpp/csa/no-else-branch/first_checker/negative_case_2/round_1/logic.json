[
  {
    "intent": "Detect an if-else if chain that ends without a final else branch, because the rule requires every conditional chain with one or more else if clauses to explicitly include an else.",
    "trigger": "An `if` statement with at least one `else if` child where the terminal branch is missing and control falls through to following statements instead of an explicit `else` block.",
    "constraints": [
      "Apply only to chained conditionals that contain one or more `else if` branches.",
      "Flag the pattern even when the missing `else` is followed by a `return`, `break`, or other statement outside the chain.",
      "Do not require the `else` body to contain logic; an empty `else` with an explanatory comment is compliant.",
      "Do not flag a simple `if` without any `else if` branches."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "getElseLoc",
      "getElseStmt",
      "CompoundStmt",
      "AST match ifStmt",
      "clang::IfStmt"
    ]
  },
  {
    "intent": "Identify the end of a conditional chain so the checker can distinguish a complete `if / else if / else` structure from an incomplete one.",
    "trigger": "Traversal of nested `IfStmt` nodes where each `else` branch is itself another `IfStmt`, continuing until the final terminal branch is reached.",
    "constraints": [
      "Treat a nested `IfStmt` in the `else` position as an `else if` continuation.",
      "Only the terminal branch of the chain determines compliance.",
      "A terminal `else` may be empty, but it must exist syntactically.",
      "Chains can be nested across arbitrary depth."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "IfStmt::getThen",
      "IgnoreImplicit",
      "Expr::IgnoreParenImpCasts",
      "RecursiveASTVisitor",
      "ASTContext",
      "Stmt"
    ]
  },
  {
    "intent": "Treat an empty final else block as compliant when it is explicitly present and optionally annotated with a comment.",
    "trigger": "A complete `if / else if / else` chain where the final `else` contains no executable statements or only a comment.",
    "constraints": [
      "Do not require non-empty statements inside the final `else`.",
      "Do not infer compliance from comments alone if the `else` keyword and block are absent.",
      "Comments may be used as guidance but are not a substitute for the missing branch.",
      "Structural presence of `else` is the only required condition."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "CompoundStmt",
      "CompoundStmt::body_empty",
      "SourceManager",
      "Lexer::getSourceText",
      "getElseLoc"
    ]
  },
  {
    "intent": "Report a violation when an `if-else if` chain omits the final else and the subsequent code becomes the implicit fallthrough path.",
    "trigger": "A chain like `if (...) { ... } else if (...) { ... }` with no final `else`, followed by ordinary code in the enclosing scope.",
    "constraints": [
      "The diagnostic should point to the missing terminal branch or the end of the chain.",
      "The checker should not depend on semantic analysis of the branch bodies.",
      "The violation is structural, not dataflow-based.",
      "Avoid false positives on `if` statements that are not part of a chain."
    ],
    "csa_api_search_terms": [
      "PathSensitiveBugReporter",
      "CheckerContext",
      "IfStmt",
      "getSourceRange",
      "SourceLocation",
      "BugReport",
      "PathDiagnosticLocation"
    ]
  },
  {
    "intent": "Support matching on canonical conditional-chain shape in Clang AST rather than textual formatting.",
    "trigger": "Source code that may span multiple lines, include braces or formatting variations, but still forms an `if / else if / else` or incomplete `if / else if` structure.",
    "constraints": [
      "Do not rely on indentation or brace style.",
      "Handle multi-line and single-line forms equivalently.",
      "Recognize the AST shape of nested `IfStmt` nodes in the `else` branch.",
      "Ignore unrelated trailing statements after the chain."
    ],
    "csa_api_search_terms": [
      "ASTMatchers",
      "ifStmt",
      "hasElse",
      "hasDescendant",
      "stmt",
      "clang::ast_matchers",
      "IfStmt"
    ]
  }
]