[
  {
    "intent": "Detect an `if` / `else if` chain that does not end with an explicit final `else` branch.",
    "trigger": "An `ifStmt` has one or more `else if` branches, and the last branch in the chain is followed directly by a statement outside the conditional instead of an `else` body.",
    "constraints": [
      "Only flag chains that contain at least one `else if`.",
      "The final `else` must exist explicitly, even if its body is empty.",
      "Do not require the `else` body to contain meaningful logic; an empty `else` with a comment is acceptable.",
      "Do not flag a simple `if` without any `else if` branches.",
      "Structural check only: do not inspect the semantics of conditions or statements inside the `else` body."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "CompoundStmt",
      "hasElse",
      "getElse",
      "getThen",
      "isIfStmt",
      "AST match ifStmt",
      "else if chain",
      "conditional branch structure"
    ]
  }
]