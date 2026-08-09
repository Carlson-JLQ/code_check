[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted, so the conditional structure does not explicitly cover all remaining cases.",
    "trigger": "A chained conditional contains one or more `else if` clauses and the last branch before control continues is not an `else` block.",
    "constraints": [
      "Only match conditional chains that actually include at least one `else if`.",
      "Do not flag a simple `if` without any `else if` clauses.",
      "Do not require the final `else` body to contain executable statements; an explicit empty `else` with a comment is acceptable.",
      "Check structural presence of the final `else`, not semantic completeness of the code inside it.",
      "Ignore unrelated nested `if` statements that form separate conditional structures."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "getThen",
      "ConditionVariable",
      "AST match ifStmt hasDescendant elseIf",
      "if-else chain",
      "clang AST IfStmt else branch"
    ]
  }
]