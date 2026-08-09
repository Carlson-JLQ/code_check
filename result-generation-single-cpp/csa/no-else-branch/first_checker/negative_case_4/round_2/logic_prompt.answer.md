[
  {
    "intent": "Detect if-else if chains that omit a final else branch and require the chain to end with an explicit else, even when that else block is empty.",
    "trigger": "An `if` statement has one or more `else if` branches, and the last branch in the chain is not followed by an `else` statement.",
    "constraints": [
      "Apply only to conditional chains that contain at least one `else if`.",
      "Treat the final `else` as mandatory for structural completeness, regardless of whether the branch contains executable statements.",
      "Accept an empty `else` only if it is explicitly present and may contain a comment such as `Other cases not handled`.",
      "Do not flag a simple `if` without `else if` branches.",
      "Do not inspect branch semantics or return/exit behavior; the check is structural only."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElse",
      "getElse",
      "getThen",
      "CompoundStmt",
      "clang::StmtVisitor",
      "clang::ast_matchers::ifStmt",
      "hasElse(ifStmt())",
      "cascading if",
      "else if chain"
    ]
  }
]