[
  {
    "intent": "Detect an if-else if statement chain whose final else branch is omitted.",
    "trigger": "An `if` statement has one or more `else if` branches, and control flows directly after the chain without an explicit final `else` block.",
    "constraints": [
      "Apply only when the conditional structure contains at least one `else if` branch.",
      "Flag the chain even if the following code would execute for all remaining cases.",
      "Do not require specific statements inside the final `else`; structural presence is sufficient.",
      "Treat an empty final `else` as compliant only if it is explicitly written and may contain only a comment."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "hasElseStorage",
      "CompoundStmt",
      "clang::Stmt",
      "RecursiveASTVisitor",
      "AST_MATCHER(ifStmt)"
    ]
  },
  {
    "intent": "Distinguish compliant conditional chains that explicitly include a terminal else branch.",
    "trigger": "An `if` / `else if` chain ends with an explicit `else` block, including an empty block with a comment.",
    "constraints": [
      "Do not emit a diagnostic when the final `else` exists.",
      "Consider both non-empty and empty compound `else` bodies as compliant.",
      "Ignore the semantic content of the `else` body; only the presence of the branch matters.",
      "Handle nested `if` constructs carefully so that only true `else if` chains are evaluated."
    ],
    "csa_api_search_terms": [
      "IfStmt",
      "getElse",
      "isIfStmt",
      "getThen",
      "Stmt::IgnoreContainers",
      "ASTContext",
      "SourceManager"
    ]
  },
  {
    "intent": "Walk an `if` statement chain to determine whether any `else if` appears before the missing final `else`.",
    "trigger": "Traversal of nested `IfStmt` nodes reveals a chain pattern where an `else` substatement is itself an `if`, and the chain terminates without a terminal non-`if` `else` branch.",
    "constraints": [
      "Follow chained `else if` links recursively until the terminal branch is reached.",
      "Only report when the chain length is at least two decision points (`if` plus one `else if`).",
      "Do not confuse nested `if` statements inside a branch with an `else if` chain.",
      "Preserve precise source location for the missing-else diagnostic."
    ],
    "csa_api_search_terms": [
      "IfStmt::getElse",
      "isa<IfStmt>",
      "dyn_cast<IfStmt>",
      "RecursiveASTVisitor",
      "AST_MATCHER_P",
      "SourceLocation"
    ]
  },
  {
    "intent": "Identify the exact location where the final else branch should be inserted for diagnostics.",
    "trigger": "A qualifying `if-else if` chain is found without a terminal `else`, requiring a checker message at the end of the chain.",
    "constraints": [
      "Anchor the report on the last `else if` branch or the closing brace of the final then-branch, depending on available source locations.",
      "Use spelling locations from the AST rather than token text heuristics when possible.",
      "Do not flag standalone `if` statements without `else if` branches.",
      "Allow comment-only final `else` branches to satisfy the rule."
    ],
    "csa_api_search_terms": [
      "getBeginLoc",
      "getEndLoc",
      "getElseLoc",
      "getThenLoc",
      "SourceRange",
      "Lexer::getSourceText",
      "BugReporter"
    ]
  }
]