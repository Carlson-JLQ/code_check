[
  {
    "intent": "Detect an if-else if chain whose final branch is omitted, because the rule requires an explicit final else for every conditional chain containing one or more else-if branches.",
    "trigger": "A conditional statement starts with `if` and contains at least one `else if`, but the last reachable branch is followed directly by the next statement instead of an `else` compound statement.",
    "constraints": [
      "The chain must be structural, not semantic: flag the case even when the uncovered path falls through to a return or other statement after the chain.",
      "Do not flag a plain `if` without any `else if` branches.",
      "Do not flag chains that already end with an explicit `else`, including an empty `else` block with only comments.",
      "Handle nested `if` statements separately from a single `if-else if` chain."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "hasElseStorageDuration",
      "clang::IfStmt",
      "AST match ifStmt hasDescendant elseStmt",
      "stmt(ifStmt)",
      "getElseLoc"
    ]
  },
  {
    "intent": "Identify multi-branch conditional chains in the AST so the checker can determine whether the final `else` branch exists after one or more `else if` clauses.",
    "trigger": "An `IfStmt` whose `else` arm is itself another `IfStmt`, repeated one or more times, indicating an `if-else if` ladder.",
    "constraints": [
      "Traverse the `else` chain until the terminal branch is reached.",
      "Only report when the terminal branch is missing, not merely when intermediate `else if` branches exist.",
      "The presence of comments in source text should not count as an `else` branch unless an actual `else` statement node exists.",
      "Ignore formatting differences such as brace style or single-line versus multi-line bodies."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "dyn_cast<IfStmt>",
      "isa<IfStmt>",
      "ignoreParenCasts",
      "RecursiveASTVisitor",
      "AST match ifStmt(hasElse(ifStmt()))",
      "Stmt::children"
    ]
  },
  {
    "intent": "Flag a violation when the code reaches the statement immediately after an `if-else if` ladder without an explicit terminal `else`, since that indicates the final branch was omitted.",
    "trigger": "An `if` chain with one or more `else if` branches is followed by a sibling statement in the same compound scope instead of a terminal `else` branch.",
    "constraints": [
      "The checker should verify the control-flow shape only; it should not require unreachable-code analysis.",
      "The rule applies even if the subsequent statement is a return, because the violation is the omitted `else`, not the post-chain behavior.",
      "Do not infer compliance from comments such as `/* else omitted intentionally */`.",
      "Report once per chain, not once per missing branch node."
    ],
    "csa_api_search_terms": [
      "CFG",
      "CFGBlock",
      "IfStmt",
      "ParentMapContext",
      "CompoundStmt",
      "StmtFinder",
      "ASTContext",
      "getSourceRange"
    ]
  },
  {
    "intent": "Support compliant empty `else` branches so the checker does not raise false positives when the terminal branch exists but contains only comments or no executable statements.",
    "trigger": "A terminal `else` branch is present syntactically, but its body is empty or contains only non-executable content.",
    "constraints": [
      "Treat an explicit `else {}` as compliant.",
      "Treat an explicit `else` with comments as compliant if the `else` node exists in the AST/source.",
      "Do not require any specific action inside the `else` branch.",
      "Comments should not be parsed as logic; they are only evidence that the branch was intentionally left empty."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "CompoundStmt::body_empty",
      "SourceManager",
      "Lexer::getSourceText",
      "FullSourceLoc",
      "getBeginLoc",
      "getEndLoc"
    ]
  },
  {
    "intent": "Produce a diagnostic that explicitly names omission of the final `else` branch in an `if-else if` chain.",
    "trigger": "A detected `if-else if` chain has no terminal `else` branch.",
    "constraints": [
      "Message should be tied to the missing `else` branch, not to the condition expressions.",
      "Keep the diagnostic stable across different condition contents and nesting depth.",
      "Use a single rule identifier for the checker so test expectations can match it reliably.",
      "The diagnostic should support source-range highlighting on the final `else if` or the end of the chain."
    ],
    "csa_api_search_terms": [
      "BugReporter",
      "PathDiagnosticLocation",
      "CheckerContext",
      "emitReport",
      "BuiltinBug",
      "PathSensitiveBugReport",
      "SourceRange",
      "DiagEngine"
    ]
  }
]