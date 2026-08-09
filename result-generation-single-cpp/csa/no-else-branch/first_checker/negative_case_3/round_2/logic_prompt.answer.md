[
  {
    "intent": "Detect conditional chains that contain one or more `else if` branches but omit the final `else` branch.",
    "trigger": "An `if` statement whose `else` subtree contains at least one nested `if` (`else if`) and the chain terminates without a final `else` statement.",
    "constraints": [
      "Only flag chains that structurally include one or more `else if` branches.",
      "Do not require any specific logic inside the `else` branch; its presence is sufficient.",
      "Treat an explicit empty `else` block with a comment as compliant.",
      "Do not flag a plain `if` without any `else if` branches.",
      "Do not flag a complete `if` / `else if` / `else` chain."
    ],
    "CSA API search terms": [
      "IfStmt",
      "getElse",
      "hasElseStorage",
      "CompoundStmt",
      "RecursiveASTVisitor",
      "Stmt::child_begin",
      "clang::ast_matchers::ifStmt",
      "hasElse"
    ]
  }
]