[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted, because every conditional chain with one or more else if branches must explicitly end with an else.",
    "trigger": "An `if` statement has at least one `else if` branch, and the chain ends without a final `else` clause.",
    "constraints": [
      "Only apply to conditional chains that contain one or more `else if` branches.",
      "The violation is structural: the checker does not inspect whether omitted logic would have been executed elsewhere.",
      "A final `else` may be empty, but it must still be present and may contain a comment such as `Other cases not handled`."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "AST_MATCHER ifStmt",
      "hasElse",
      "getElse",
      "isElseIf",
      "hasElseStmt",
      "getElseLoc"
    ]
  },
  {
    "intent": "Treat a chain as compliant when it includes a final else branch after one or more else if branches, regardless of whether the else body is empty or contains only comments.",
    "trigger": "An `if` / `else if` chain is present and the final branch is an explicit `else` statement.",
    "constraints": [
      "Do not require the else branch to perform any computation.",
      "Do not flag empty else blocks if they are explicitly written.",
      "The presence of a final `else` satisfies the rule even when its body is a no-op."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "CompoundStmt",
      "hasElse",
      "getElse",
      "isCompoundStmt",
      "AST_MATCHER unless"
    ]
  },
  {
    "intent": "Ignore simple if statements and if-else statements that do not contain any else if branches, since the rule only applies to conditional chains with at least one else if.",
    "trigger": "A conditional statement has no `else if` branches, even if it has an `else` or lacks one entirely.",
    "constraints": [
      "Do not diagnose single `if` statements.",
      "Do not diagnose direct `if` / `else` forms without any intermediate `else if`.",
      "The chain-length requirement is mandatory before reporting."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "AST_MATCHER ifStmt",
      "Stmt::IgnoreParenImpCasts"
    ]
  },
  {
    "intent": "Report the exact location of the missing final else branch so the diagnostic points at the end of the conditional chain that needs completion.",
    "trigger": "The analyzer confirms an `if-else if` chain and finds that the last reachable branch is an `else if` instead of an explicit `else`.",
    "constraints": [
      "Diagnostic should attach to the closing point of the chain or the last `else if` branch.",
      "The checker should distinguish the absence of `else` from an empty `else` block.",
      "Use a message aligned with the rule that the final `else` is required."
    ],
    "csa_api_search_terms": [
      "SourceLocation",
      "SourceRange",
      "IfStmt",
      "getElseLoc",
      "getRParenLoc",
      "getEndLoc",
      "DiagnosticsEngine"
    ]
  }
]