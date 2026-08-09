[
  {
    "intent": "Detect an if-else if chain whose final else branch is missing, because the rule requires every conditional chain containing one or more else if branches to explicitly end with an else.",
    "trigger": "An if statement has at least one else if clause, and the chain terminates without a final else clause; control continues after the chain with no explicit else block.",
    "constraints": [
      "Apply only to conditional chains that contain one or more else if branches.",
      "Treat the pattern as non-compliant even if later statements appear to cover the missing case.",
      "Do not require any particular logic inside the else branch; structural presence is the requirement.",
      "The final else may be empty, but it must be explicitly present."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "hasElseStorage",
      "isa<IfStmt>",
      "dyn_cast<IfStmt>",
      "IfStmt::getElse()",
      "Else if chain"
    ]
  },
  {
    "intent": "Confirm compliance when an if-else if chain includes a final else branch, regardless of whether the else body is empty or contains statements.",
    "trigger": "An if statement has one or more else if clauses and the final branch is an explicit else statement, including an empty compound statement or comment-only body.",
    "constraints": [
      "Accept empty else bodies as compliant if the else branch is explicitly written.",
      "Ignore the semantic content of the else body; only the presence of the else branch matters.",
      "Require detection across nested if statements only when they form a single else-if chain, not unrelated nested conditionals."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "CompoundStmt",
      "Stmt::children",
      "hasElseStorage",
      "getThen",
      "getCond"
    ]
  },
  {
    "intent": "Differentiate a simple if statement from an if-else if chain so the checker does not flag conditionals that have no else if branches.",
    "trigger": "An if statement has no else if clauses, even if it lacks a final else branch.",
    "constraints": [
      "Do not report plain if statements without else if branches.",
      "Only chains with at least one else if clause are subject to the rule.",
      "Avoid false positives on nested independent if statements that are not part of one chain."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "getThen",
      "getCond",
      "isSingleStmt",
      "children"
    ]
  }
]