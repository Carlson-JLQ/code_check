[
  {
    "intent": "Detect direct assignment expressions used as the controlling expression of a logical statement, especially `if`, where the assignment result is implicitly converted to boolean and may hide a comparison bug.",
    "trigger": "A conditional statement uses an assignment expression as its condition, for example `if (a = b)`, `while (x = f())`, or `for (; y = z; )`.",
    "constraints": [
      "Report only when the assignment expression is directly inside a logical/evaluated condition.",
      "Treat any assignment operator form as a violation, including simple assignment and compound assignment when used as the condition value.",
      "Do not report when the assignment is outside the condition and the condition uses a comparison, such as `a = b; if (a == 0)`.",
      "Do not report ordinary non-conditional assignments, initializer assignments, or assignments used in non-logical contexts.",
      "The rule applies regardless of whether the assignment result is later compared or wrapped in another expression, if the assignment itself is part of the logical evaluation."
    ],
    "CSA API search terms": [
      "Stmt::IfStmt",
      "Stmt::WhileStmt",
      "Stmt::ForStmt",
      "Expr::isAssignmentOp",
      "BinaryOperator::isAssignmentOp",
      "BinaryOperator",
      "Expr::IgnoreParenImpCasts",
      "AST match assignment in condition",
      "clang::ast_matchers::ifStmt",
      "clang::ast_matchers::whileStmt",
      "clang::ast_matchers::forStmt",
      "clang::ast_matchers::binaryOperator"
    ]
  }
]