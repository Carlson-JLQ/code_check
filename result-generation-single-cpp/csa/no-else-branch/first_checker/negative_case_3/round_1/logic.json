[
  {
    "intent": "Detect an if / else-if chain that omits the required final else branch, since the rule requires every conditional chain with one or more else-if branches to end in an explicit else.",
    "trigger": "A compound `if` statement contains at least one `else if` branch, and the final branch before the next sibling statement is not an `else` body.",
    "constraints": [
      "Only apply when the conditional structure includes one or more `else if` branches.",
      "Do not flag a simple `if` with no `else if` branches.",
      "Do not flag chains that end with an explicit `else`, even if that `else` block is empty or comment-only.",
      "The violation is structural: the check does not require the `else` body to contain executable logic."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "hasElseStorage",
      "AST match if statement",
      "clang::IfStmt",
      "else if chain",
      "nested IfStmt in else branch"
    ]
  },
  {
    "intent": "Recognize chains where `else if` is represented as a nested `IfStmt` in the `else` branch, and verify that the final nested branch still has an explicit terminating `else`.",
    "trigger": "Traversing an `IfStmt` whose `else` branch is itself another `IfStmt`, continuing until the terminal branch is reached and finding that the terminal `IfStmt` has no `else`.",
    "constraints": [
      "Handle syntactic sugar in C and C++ where `else if` is parsed as `else { if (...) ... }` in the AST.",
      "Flag only the terminal missing `else`, not intermediate `else if` nodes.",
      "Respect braces and comments as irrelevant to compliance; only the presence of an explicit `else` node matters."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "IfStmt::getElse()->IgnoreParenImpCasts",
      "dyn_cast<IfStmt>",
      "AST walk recursive IfStmt",
      "RecursiveASTVisitor",
      "Stmt::children",
      "Expr::IgnoreParenImpCasts"
    ]
  },
  {
    "intent": "Treat an explicit empty `else` block as compliant, including cases where the block exists only to satisfy the structural requirement and may contain a comment.",
    "trigger": "An `if / else-if` chain ends with `else {}` or `else { /* comment */ }` rather than omitting the else branch.",
    "constraints": [
      "Do not require statements inside the final `else` block.",
      "Do not reject an empty compound statement in the final `else` branch.",
      "Comments may be present but are not required for compliance by the analyzer unless the project chooses to inspect source text."
    ],
    "csa_api_search_terms": [
      "CompoundStmt",
      "IfStmt::getElse",
      "CompoundStmt::body_empty",
      "SourceManager",
      "Lexer::getSourceText",
      "FullSourceLoc"
    ]
  },
  {
    "intent": "Differentiate between a plain `if` statement and a multi-branch `if-else if` chain so the checker only enforces the rule when the chain actually contains one or more `else if` clauses.",
    "trigger": "An `IfStmt` is encountered and its `else` branch chain contains at least one nested `IfStmt` representing `else if`.",
    "constraints": [
      "Do not flag standalone `if` statements with no `else` and no `else if`.",
      "Do not flag `if-else` statements that have a final else but no `else if` chain.",
      "The minimum condition for enforcement is at least one `else if` branch in the chain."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElse",
      "getElse",
      "ASTContext",
      "StmtClass::IfStmtClass",
      "switch on Stmt kind"
    ]
  },
  {
    "intent": "Emit a diagnostic when the final `else` is missing at the end of a qualifying chain, matching the rule identifier used by the test case.",
    "trigger": "A qualifying `if / else-if` chain terminates without an explicit `else` branch, producing a checker diagnostic for omitted else handling.",
    "constraints": [
      "Diagnostic should target the terminating `if` chain location that lacks `else`.",
      "Message should describe omission of the `else` branch, not missing runtime logic.",
      "Support the rule id used by tests: `gjb8114-r-1-4-1`."
    ],
    "csa_api_search_terms": [
      "BugReporter",
      "PathSensitiveBugReport",
      "CheckerContext",
      "emitReport",
      "diag::",
      "BugType",
      "SourceRange"
    ]
  }
]