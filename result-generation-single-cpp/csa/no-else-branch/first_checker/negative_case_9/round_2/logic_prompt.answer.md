[
  {
    "intent": "Detect conditional chains that use one or more `else if` branches but omit the final `else` branch.",
    "trigger": "An `if` statement whose `else` chain contains at least one `else if`, and the chain terminates without an explicit final `else` block.",
    "constraints": [
      "Only flag chained conditionals that include one or more `else if` branches.",
      "Require an explicit final `else` branch even when it is empty or contains only a comment.",
      "Do not flag a plain `if` without `else if` branches.",
      "Do not inspect the semantics of the `else` body; only verify structural presence."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "getElseLoc",
      "ElseIf",
      "ASTMatcher IfStmt hasElse",
      "clang::ast_matchers::ifStmt",
      "clang::IfStmt"
    ]
  }
]