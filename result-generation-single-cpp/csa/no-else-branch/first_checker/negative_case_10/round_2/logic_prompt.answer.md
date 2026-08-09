[
  {
    "intent": "Detect an if-else if chain that does not include a final else branch, because the rule requires every conditional chain with one or more else if branches to explicitly terminate with else.",
    "trigger": "Match an `if` statement whose `else` arm is another `if` statement one or more times, and the outermost chain ends without a final `else` compound statement or single statement.",
    "constraints": [
      "Only apply when the conditional structure contains at least one `else if` branch.",
      "Treat a missing final `else` as a violation even if execution continues with a following `return`, `break`, or other statement.",
      "Do not flag plain `if` statements without any `else if` branches.",
      "Do not flag chains that already include a final `else`, regardless of whether that `else` body is empty or contains only comments."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "hasElseStorage",
      "getElse",
      "getThen",
      "stmt::IfStmt",
      "clang::IfStmt"
    ]
  },
  {
    "intent": "Verify that a complete if-else if chain is structurally closed by an explicit final else branch, including the case where the else body is intentionally empty but present.",
    "trigger": "Find nested `IfStmt` nodes representing an `if-else if` chain and inspect whether the terminal branch is an explicit `else` node rather than absent.",
    "constraints": [
      "The rule is structural, not semantic: do not require the else body to contain executable logic.",
      "Accept an explicit empty `else {}` as compliant if it is present.",
      "Accept an `else` containing only comments as compliant if the parser still yields an explicit else branch.",
      "Flag the construct only when the chain terminates without an else arm."
    ],
    "csa_api_search_terms": [
      "ASTContext",
      "RecursiveASTVisitor",
      "IfStmt::getElse",
      "ParenListExpr",
      "CompoundStmt"
    ]
  },
  {
    "intent": "Identify the terminal missing-else condition in a multi-branch else-if ladder so the diagnostic can point at the specific chain head or final `else if` node.",
    "trigger": "Traverse chained `IfStmt` nodes through successive `else` arms until reaching the final node; if that final node has no `else` branch, emit the finding.",
    "constraints": [
      "Handle chains of any length, including two-branch and multi-branch ladders.",
      "The final `else` must be explicit and attached to the last `if` in the ladder.",
      "Ignore indentation or formatting; rely on AST structure only.",
      "Do not misclassify unrelated nested `if` statements that are not part of an `else if` chain."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "IfStmt::getConditionVariableDeclStmt",
      "ASTMatcher",
      "hasDescendant",
      "unless"
    ]
  },
  {
    "intent": "Support a checker message for omitted else branches in else-if chains and keep the rule limited to conditional-chain integrity rather than branch content analysis.",
    "trigger": "When a chain with one or more `else if` branches lacks a terminal `else`, report a rule violation even if all observed branches appear exhaustive by domain knowledge.",
    "constraints": [
      "Do not attempt dataflow or path-exhaustiveness reasoning.",
      "Do not infer that a missing else is harmless because a later statement returns or aborts.",
      "Compliant examples are defined only by the presence of the final else branch.",
      "Any diagnostic should be tied to the conditional chain, not to specific expressions like `isdigit`, `isalpha`, or `isspace`."
    ],
    "csa_api_search_terms": [
      "BugReporter",
      "PathSensitiveBugReporter",
      "CheckerContext",
      "BranchCondition",
      "IfStmt"
    ]
  }
]