[
  {
    "intent": "Detect an `if` / `else if` chain that omits the final `else` branch and therefore fails the rule requiring every conditional chain with one or more `else if` branches to end with an explicit `else`.",
    "trigger": "An `IfStmt` represents a chain containing at least one `else if` and the chain terminates without an `else` block attached to the final branch.",
    "constraints": [
      "Only apply when the conditional structure contains one or more `else if` branches.",
      "A plain `if` with no `else if` is out of scope.",
      "The final `else` must be syntactically present, even if its body is empty or only contains a comment.",
      "Do not require any specific statements inside the `else` body; structural presence is the rule.",
      "Treat `else if` as a nested `IfStmt` in the `else` branch and walk to the end of the chain."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "hasElseStorage",
      "isa<IfStmt>",
      "dyn_cast<IfStmt>",
      "Stmt::children",
      "RecursiveASTVisitor::VisitIfStmt"
    ]
  },
  {
    "intent": "Confirm compliance when an `if` / `else if` chain includes a final explicit `else` branch, including the case where the `else` body is empty or contains only a comment.",
    "trigger": "An `IfStmt` chain with one or more `else if` branches ends in an explicit non-null `else` statement.",
    "constraints": [
      "The final `else` must exist as a distinct AST branch.",
      "An empty compound statement `{}` should still count as compliant.",
      "A comment-only `else` body is compliant if the parser preserves the empty compound structure; comments themselves are not relied upon in AST analysis.",
      "The checker should not inspect the semantic content of the `else` body."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "CompoundStmt",
      "isCompoundStmt",
      "RecursiveASTVisitor",
      "ASTContext",
      "Stmt::IgnoreParenImpCasts",
      "Expr::isDefaultArgument"
    ]
  },
  {
    "intent": "Identify the end of an `if` / `else if` chain so the checker can distinguish a missing final `else` from a chain whose final branch is already present.",
    "trigger": "Traversal over nested `IfStmt` nodes through successive `else if` branches reaches the last `IfStmt` in the chain.",
    "constraints": [
      "Follow nested `IfStmt` nodes only through the `else` branch when it itself is another `IfStmt`.",
      "Stop when the `else` branch is null or is not an `IfStmt`.",
      "This logic should not flag unrelated nested `if` statements that are not part of an `else if` chain."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getElseLoc",
      "getConditionVariable",
      "RecursiveASTVisitor::TraverseIfStmt",
      "ASTMatcher",
      "hasDescendant"
    ]
  },
  {
    "intent": "Report a diagnostic when a chain with `else if` branches ends in a statement after the final `else if` instead of an explicit `else` branch.",
    "trigger": "The AST shows an `if` chain where the last `else if` is followed by the next statement in the enclosing scope rather than an `else` branch.",
    "constraints": [
      "The warning should point at the start of the chain or the location of the missing `else` opportunity.",
      "Do not report when there is no `else if` at all.",
      "Do not report when the chain ends with an explicit `else` containing an empty block.",
      "The message should describe omission of the `else` branch, not missing logic inside `else`."
    ],
    "csa_api_search_terms": [
      "PathSensitiveBugReport",
      "BugReporter",
      "SourceManager",
      "IfStmt::getElse",
      "FullSourceLoc",
      "SourceRange",
      "diagnoseIfStmt"
    ]
  }
]