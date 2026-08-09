[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted, because the rule requires every conditional chain with one or more else if branches to end with an explicit else.",
    "trigger": "An `if` statement has at least one `else if` sibling in its chained conditional structure, and the chain terminates without a final `else` body.",
    "constraints": [
      "Only apply when the conditional structure contains one or more `else if` branches.",
      "Treat an empty final `else` with an explicit comment as compliant.",
      "Do not flag plain `if` statements without any `else if` branches.",
      "Do not inspect the contents of the final `else`; only its structural presence matters."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "CompoundStmt",
      "Else if chain",
      "AST match ifStmt hasElse",
      "RecursiveASTVisitor IfStmt",
      "Stmt::children"
    ]
  },
  {
    "intent": "Identify conditional chains where `else if` branches exist but the final `else` is implicitly absent because control falls through to the next statement.",
    "trigger": "The analyzer sees an `if`/`else if` chain followed immediately by a non-`else` statement at the same lexical nesting level, indicating the chain ended without a final `else` block.",
    "constraints": [
      "Distinguish chain termination from nested `if` statements inside branch bodies.",
      "Only report when the top-level chain with `else if` branches lacks an explicit final `else`.",
      "Ignore cases where the final `else` is present but empty."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "ASTContext",
      "SourceManager",
      "ParentMapContext",
      "RecursiveASTVisitor",
      "StmtLoc",
      "SourceRange"
    ]
  },
  {
    "intent": "Handle chained conditionals across multiple `else if` levels and confirm that the last branch in the chain is explicitly represented as `else`.",
    "trigger": "Traversal discovers a linked sequence of `IfStmt` nodes through `getElse()` where the terminal node is another `IfStmt` rather than an `else` block.",
    "constraints": [
      "Follow nested `IfStmt` nodes through the `else` arm to determine whether the chain ends in an actual `else` body.",
      "A terminal `IfStmt` without an `else` is non-compliant when the chain includes `else if` branches.",
      "Do not require a specific statement in the final `else`; an empty compound statement is acceptable with a comment."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "dyn_cast<IfStmt>",
      "isa<IfStmt>",
      "RecursiveASTVisitor::VisitIfStmt",
      "AST match unless",
      "hasElse"
    ]
  },
  {
    "intent": "Differentiate compliant empty final `else` branches from missing branches, so that a no-op `else` is accepted when explicitly written.",
    "trigger": "A conditional chain with one or more `else if` branches ends in `else {}` or `else { /* comment */ }`.",
    "constraints": [
      "Empty `else` blocks are valid if explicitly present.",
      "Comments inside the empty `else` are allowed but not required for detection.",
      "Do not flag based on lack of executable statements inside the `else`."
    ],
    "csa_api_search_terms": [
      "CompoundStmt",
      "IfStmt::getElse",
      "Stmt::isEmpty",
      "ASTContext",
      "SourceRange",
      "Lexer::getSourceText"
    ]
  }
]