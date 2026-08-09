[
  {
    "intent": "Detect conditional chains that contain one or more `else if` branches but do not end with an explicit final `else` branch.",
    "trigger": "An `if` statement whose `else` arm is another `if` (`else if`) in the same chain, and traversal reaches the end of the chain without finding a terminal `else` block.",
    "constraints": [
      "Only flag chains with at least one `else if` branch.",
      "The final `else` must be syntactically present, even if its body is empty.",
      "Do not require any specific statements inside the `else` body.",
      "Empty `else` bodies are acceptable if they contain an appropriate comment.",
      "Do not flag single `if` statements or `if-else` statements that do not use `else if`."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "ElseIf",
      "CompoundStmt",
      "Stmt::children",
      "RecursiveASTVisitor<IfStmt>",
      "hasElse",
      "isIfStmt"
    ]
  },
  {
    "intent": "Verify that an `if-else if` chain is structurally complete by ensuring the terminal branch is an explicit `else` rather than fall-through to subsequent code.",
    "trigger": "A chain where an `IfStmt` has an `else if` descendant and the final branch is missing, so control exits the chain directly into following statements.",
    "constraints": [
      "The checker should reason about the full `if / else if / else if / ...` chain as one structure.",
      "The absence of a terminal `else` is the defect, regardless of the correctness of condition expressions.",
      "The checker should ignore runtime behavior and focus only on syntax/structure.",
      "Comments in the source do not satisfy the requirement unless an actual `else` branch exists."
    ],
    "csa_api_search_terms": [
      "clang::IfStmt",
      "ASTContext",
      "SourceManager",
      "FullSourceLoc",
      "getElse",
      "IgnoreParenImpCasts",
      "StmtClass::IfStmtClass",
      "DynTypedNode"
    ]
  },
  {
    "intent": "Allow chains that include an explicit final `else` branch, including empty `else` blocks used only to satisfy completeness.",
    "trigger": "An `if` statement chain with one or more `else if` branches followed by a terminal `else` statement, whether the body contains executable statements or only comments.",
    "constraints": [
      "Presence of the final `else` is sufficient for compliance.",
      "The content of the `else` block must not be used as a pass/fail criterion.",
      "Comment-only `else` blocks should be treated as compliant if the `else` branch exists syntactically.",
      "The checker should not require the `else` body to return, throw, or assign."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "CompoundStmt",
      "EmptyShell",
      "ASTMatcher ifStmt",
      "unless",
      "hasDescendant",
      "SourceRange",
      "Lexer::getSourceText"
    ]
  }
]