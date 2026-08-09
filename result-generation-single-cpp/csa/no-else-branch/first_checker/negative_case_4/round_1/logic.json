[
  {
    "intent": "Detect if-else if chains whose final else branch is omitted, because the rule requires every conditional chain with one or more else if branches to end with an explicit else.",
    "trigger": "An `if` statement has at least one `else if` branch, and the chain ends without a final `else` body.",
    "constraints": [
      "Only applies to conditional chains that contain one or more `else if` branches.",
      "The final `else` branch must exist explicitly, even if it is empty.",
      "An empty else is still compliant if it is present and may contain a comment such as `Other cases not handled`.",
      "Do not flag plain `if` statements without any `else if` branches.",
      "Do not inspect the contents of the `else` branch for business logic; check structural presence only."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "getElseLoc",
      "getElseIfStmt",
      "CompoundStmt",
      "Stmt::children",
      "RecursiveASTVisitor",
      "AST match ifStmt hasDescendant elseStmt",
      "clang::IfStmt"
    ]
  }
]