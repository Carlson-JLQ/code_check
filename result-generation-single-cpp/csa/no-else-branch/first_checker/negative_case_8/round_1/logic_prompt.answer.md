[
  {
    "intent": "Detect an if-else if chain whose final else branch is omitted, because the checker requires every multi-branch conditional chain to end with an explicit else.",
    "trigger": [
      "A control-flow construct is an `if` statement that contains at least one `else if` branch.",
      "The chain ends with an `if` or `else if` node whose `else` child is missing.",
      "The missing branch is structural, regardless of whether the omitted branch would be empty or contain logic."
    ],
    "constraints": [
      "Only apply when there is one or more `else if` branches in the same conditional chain.",
      "Do not flag a plain `if` without any `else if` branches.",
      "Do not require non-empty logic in the final `else`; an empty `else` with a comment is compliant.",
      "Focus on AST structure, not runtime behavior or expression semantics."
    ],
    "csa_api_search_terms": [
      "clang static analyzer checker AST if stmt else branch",
      "Stmt::IfStmt",
      "IfStmt hasElse",
      "IfStmt getElse",
      "IfStmt getElseLoc",
      "RecursiveASTVisitor IfStmt",
      "clang AST matchers ifStmt hasElse",
      "if-else if chain AST",
      "ConditionalOperator not applicable"
    ]
  },
  {
    "intent": "Verify that the checker treats an explicit empty final else branch as compliant when an if-else if chain exists.",
    "trigger": [
      "An `if` statement has one or more `else if` branches.",
      "The final branch is an explicit `else {}` or equivalent empty compound statement.",
      "The checker inspects the presence of the branch, not the amount of content inside it."
    ],
    "constraints": [
      "An empty `else` must still count as valid structural coverage.",
      "Comments inside an empty `else` may exist but are not required for detection.",
      "Do not report based on branch body emptiness alone."
    ],
    "csa_api_search_terms": [
      "IfStmt getElse",
      "CompoundStmt empty",
      "AST matcher hasElse",
      "Stmt body empty compound",
      "clang AST ifStmt has(elseStmt())"
    ]
  },
  {
    "intent": "Reject conditional chains where the final else is missing even though the preceding branches are written as `else if` clauses.",
    "trigger": [
      "Source contains `if (...) ... else if (...) ...` with any number of chained `else if` nodes.",
      "The chain terminates directly with a statement after the last `else if`, rather than with an explicit `else` block.",
      "A trailing `return`, `break`, or other statement outside the chain is not an acceptable substitute for the missing `else`."
    ],
    "constraints": [
      "The checker should not infer that later code covers the missing else case.",
      "The checker should not depend on whether all branches return.",
      "The checker should report only when the chain lacks an explicit final else."
    ],
    "csa_api_search_terms": [
      "IfStmt else missing",
      "AST parent chain ifStmt",
      "clang AST matcher else if chain",
      "getElse null",
      "build CFG if statement else branch"
    ]
  }
]