[
  {
    "intent": "Detect any if-else if chain where the final else branch is omitted.",
    "trigger": "An `if` statement with one or more `else if` branches is present, and the chain ends without a terminal `else` clause.",
    "constraints": [
      "Only apply when the conditional structure contains at least one `else if` branch.",
      "Report the issue regardless of whether the omitted `else` would be empty or contain logic.",
      "Do not flag a plain `if` without `else if` branches.",
      "Do not flag chains that already include a final `else`, even if the body is empty or comment-only."
    ],
    "CSA API search terms": [
      "IfStmt",
      "getElse",
      "hasElseStorage",
      "dyn_cast<IfStmt>",
      "IfStmt::getElse()"
    ]
  },
  {
    "intent": "Recognize nested conditional chains and ensure each distinct if-else if structure is validated independently.",
    "trigger": "A nested `if` contains its own `else if` chain, or an outer `if` contains another conditional chain in one branch.",
    "constraints": [
      "Evaluate each `if-else if` chain by its own syntactic structure.",
      "An inner chain missing a final `else` is a separate finding from an outer chain missing a final `else`.",
      "Do not infer compliance of one chain from the presence of an `else` in a different nested chain."
    ],
    "CSA API search terms": [
      "IfStmt",
      "getThen",
      "getElse",
      "children",
      "StmtVisitor",
      "RecursiveASTVisitor"
    ]
  },
  {
    "intent": "Allow compliant chains where a final else exists but contains no executable statements.",
    "trigger": "An `if-else if` chain ends with an explicit `else` whose body is empty or only contains comments.",
    "constraints": [
      "Treat an explicit empty `else` as compliant.",
      "Treat a comment-only `else` as compliant if the AST still contains the explicit branch.",
      "Do not require specific logic inside the final `else`."
    ],
    "CSA API search terms": [
      "IfStmt",
      "CompoundStmt",
      "NullStmt",
      "getElse",
      "isEmpty"
    ]
  },
  {
    "intent": "Report the omission only when the chain structure reaches an `else if` branch and terminates without a final else.",
    "trigger": "The AST shows a chain of `IfStmt` nodes linked through `getElse()` where the last reachable branch is another `IfStmt` and there is no terminal non-`IfStmt` else body.",
    "constraints": [
      "Follow chained `IfStmt` nodes through the else arm to determine whether the structure is an `if-else if` chain.",
      "Flag only when the last chain link has no `else` branch.",
      "Avoid false positives on `if` statements whose `else` arm is a normal statement block rather than another `if`."
    ],
    "CSA API search terms": [
      "IfStmt",
      "getElse",
      "IgnoreUnlessSpelledInSource",
      "ASTContext",
      "Stmt::IgnoreParenImpCasts"
    ]
  }
]