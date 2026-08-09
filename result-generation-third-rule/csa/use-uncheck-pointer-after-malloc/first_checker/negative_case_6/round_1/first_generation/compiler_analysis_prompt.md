Analyze this CSA plugin compiler failure and return JSON with
repair_steps and api_search_terms.
Compiler output:

/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:306:11: error: binding reference of type 'SourceManager' to value of type 'const SourceManager' drops 'const' qualifier
  306 |           SM(BR.getSourceManager()) {}
      |           ^  ~~~~~~~~~~~~~~~~~~~~~
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:5:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/Decl.h:17:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/APValue.h:16:
In file included from /home/llvm/llvm-project/clang/include/clang/Basic/LLVM.h:21:
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:734:12: error: call to deleted constructor of 'clang::Expr'
  734 |     return CastInfo<X, const Y>::castFailed();
      |            ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:754:10: note: in instantiation of function template specialization 'llvm::dyn_cast_if_present<clang::Expr, std::nullptr_t>' requested here
  754 |   return dyn_cast_if_present<X>(Val);
      |          ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:313:34: note: in instantiation of function template specialization 'llvm::dyn_cast_or_null<clang::Expr, std::nullptr_t>' requested here
  313 |         if (const Expr *Parent = dyn_cast_or_null<Expr>(CE->getStmtClass() ?
      |                                  ^
/home/llvm/llvm-project/clang/include/clang/AST/Expr.h:117:3: note: 'Expr' has been explicitly marked deleted here
  117 |   Expr(const Expr&) = delete;
      |   ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:5:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/Decl.h:17:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/APValue.h:16:
In file included from /home/llvm/llvm-project/clang/include/clang/Basic/LLVM.h:21:
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:735:10: error: call to deleted constructor of 'clang::Expr'
  735 |   return CastInfo<X, const Y>::doCastIfPossible(detail::unwrapValue(Val));
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/home/llvm/llvm-project/clang/include/clang/AST/Expr.h:117:3: note: 'Expr' has been explicitly marked deleted here
  117 |   Expr(const Expr&) = delete;
      |   ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:313:25: error: no viable conversion from 'clang::Expr' to 'const Expr *'
  313 |         if (const Expr *Parent = dyn_cast_or_null<Expr>(CE->getStmtClass() ?
      |                         ^        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  314 |                                                         nullptr : nullptr)) {
      |                                                         ~~~~~~~~~~~~~~~~~~
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:5:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/Decl.h:17:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/APValue.h:16:
In file included from /home/llvm/llvm-project/clang/include/clang/Basic/LLVM.h:21:
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:490:54: error: functional-style cast from rvalue to reference type 'CastReturnType' (aka 'const clang::Expr &')
  490 |   static inline CastReturnType castFailed() { return CastReturnType(nullptr); }
      |                                                      ^~~~~~~~~~~~~~~~~~~~~~~
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:734:34: note: in instantiation of member function 'llvm::CastInfo<clang::Expr, const std::nullptr_t>::castFailed' requested here
  734 |     return CastInfo<X, const Y>::castFailed();
      |                                  ^
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:64:65: error: cannot initialize a parameter of type 'const Stmt *' with an rvalue of type 'const std::nullptr_t *'
   64 |   static inline bool doit(const From &Val) { return To::classof(&Val); }
      |                                                                 ^~~~
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:81:32: note: in instantiation of member function 'llvm::isa_impl<clang::Expr, std::nullptr_t>::doit' requested here
   81 |     return isa_impl<To, From>::doit(Val);
      |                                ^
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:137:37: note: in instantiation of member function 'llvm::isa_impl_cl<clang::Expr, const std::nullptr_t>::doit' requested here
  137 |     return isa_impl_cl<To, FromTy>::doit(Val);
      |                                     ^
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:257:58: note: in instantiation of member function 'llvm::isa_impl_wrap<clang::Expr, const std::nullptr_t, const std::nullptr_t>::doit' requested here
  257 |         typename simplify_type<const From>::SimpleType>::doit(f);
      |                                                          ^
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:493:16: note: in instantiation of member function 'llvm::CastIsPossible<clang::Expr, const std::nullptr_t>::isPossible' requested here
  493 |     if (!Self::isPossible(f))
      |                ^
/home/llvm/llvm-project/llvm/include/llvm/Support/Casting.h:735:32: note: in instantiation of member function 'llvm::CastInfo<clang::Expr, const std::nullptr_t>::doCastIfPossible' requested here
  735 |   return CastInfo<X, const Y>::doCastIfPossible(detail::unwrapValue(Val));
      |                                ^
/home/llvm/llvm-project/clang/include/clang/AST/Expr.h:1037:35: note: passing argument to parameter 'T' here
 1037 |   static bool classof(const Stmt *T) {
      |                                   ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:24:1: error: 'VisitWhileStmt' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
   24 | WHILESTMT(WhileStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:22:33: note: expanded from macro 'WHILESTMT'
   22 | #  define WHILESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:76:1: note: expanded from here
   76 | VisitWhileStmt
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:24:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromWhileStmt' requested here
   24 | WHILESTMT(WhileStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:22:33: note: expanded from macro 'WHILESTMT'
   22 | #  define WHILESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:102:1: note: expanded from here
  102 | WalkUpFromWhileStmt
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:241:10: note: implicitly declared private here
  241 |     bool VisitWhileStmt(WhileStmt *WS) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:50:1: error: 'VisitUnaryOperator' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
   50 | UNARYOPERATOR(UnaryOperator, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:48:37: note: expanded from macro 'UNARYOPERATOR'
   48 | #  define UNARYOPERATOR(Type, Base) EXPR(Type, Base)
      |                                     ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:96:1: note: expanded from here
   96 | VisitUnaryOperator
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:50:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromUnaryOperator' requested here
   50 | UNARYOPERATOR(UnaryOperator, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:48:37: note: expanded from macro 'UNARYOPERATOR'
   48 | #  define UNARYOPERATOR(Type, Base) EXPR(Type, Base)
      |                                     ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:114:1: note: expanded from here
  114 | WalkUpFromUnaryOperator
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:257:10: note: implicitly declared private here
  257 |     bool VisitUnaryOperator(UnaryOperator *UO) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:318:1: error: 'VisitMemberExpr' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
  318 | MEMBEREXPR(MemberExpr, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:316:34: note: expanded from macro 'MEMBEREXPR'
  316 | #  define MEMBEREXPR(Type, Base) EXPR(Type, Base)
      |                                  ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:118:1: note: expanded from here
  118 | VisitMemberExpr
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:318:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromMemberExpr' requested here
  318 | MEMBEREXPR(MemberExpr, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:316:34: note: expanded from macro 'MEMBEREXPR'
  316 | #  define MEMBEREXPR(Type, Base) EXPR(Type, Base)
      |                                  ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:104:1: note: expanded from here
  104 | WalkUpFromMemberExpr
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:288:10: note: implicitly declared private here
  288 |     bool VisitMemberExpr(MemberExpr *ME) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:818:1: error: 'VisitBinaryOperator' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
  818 | BINARYOPERATOR(BinaryOperator, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:816:38: note: expanded from macro 'BINARYOPERATOR'
  816 | #  define BINARYOPERATOR(Type, Base) EXPR(Type, Base)
      |                                      ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:101:1: note: expanded from here
  101 | VisitBinaryOperator
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:818:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromBinaryOperator' requested here
  818 | BINARYOPERATOR(BinaryOperator, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:816:38: note: expanded from macro 'BINARYOPERATOR'
  816 | #  define BINARYOPERATOR(Type, Base) EXPR(Type, Base)
      |                                      ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:107:1: note: expanded from here
  107 | WalkUpFromBinaryOperator
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:204:10: note: implicitly declared private here
  204 |     bool VisitBinaryOperator(BinaryOperator *BO) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:850:1: error: 'VisitArraySubscriptExpr' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
  850 | ARRAYSUBSCRIPTEXPR(ArraySubscriptExpr, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:848:42: note: expanded from macro 'ARRAYSUBSCRIPTEXPR'
  848 | #  define ARRAYSUBSCRIPTEXPR(Type, Base) EXPR(Type, Base)
      |                                          ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:121:1: note: expanded from here
  121 | VisitArraySubscriptExpr
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:850:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromArraySubscriptExpr' requested here
  850 | ARRAYSUBSCRIPTEXPR(ArraySubscriptExpr, Expr)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:848:42: note: expanded from macro 'ARRAYSUBSCRIPTEXPR'
  848 | #  define ARRAYSUBSCRIPTEXPR(Type, Base) EXPR(Type, Base)
      |                                          ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:38:28: note: expanded from macro 'EXPR'
   38 | #  define EXPR(Type, Base) VALUESTMT(Type, Base)
      |                            ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:28:33: note: expanded from macro 'VALUESTMT'
   28 | #  define VALUESTMT(Type, Base) STMT(Type, Base)
      |                                 ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:127:1: note: expanded from here
  127 | WalkUpFromArraySubscriptExpr
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:274:10: note: implicitly declared private here
  274 |     bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1676:1: error: 'VisitIfStmt' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
 1676 | IFSTMT(IfStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1674:30: note: expanded from macro 'IFSTMT'
 1674 | #  define IFSTMT(Type, Base) STMT(Type, Base)
      |                              ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:103:1: note: expanded from here
  103 | VisitIfStmt
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1676:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromIfStmt' requested here
 1676 | IFSTMT(IfStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1674:30: note: expanded from macro 'IFSTMT'
 1674 | #  define IFSTMT(Type, Base) STMT(Type, Base)
      |                              ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:106:1: note: expanded from here
  106 | WalkUpFromIfStmt
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:236:10: note: implicitly declared private here
  236 |     bool VisitIfStmt(IfStmt *IS) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1688:1: error: 'VisitForStmt' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
 1688 | FORSTMT(ForStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1686:31: note: expanded from macro 'FORSTMT'
 1686 | #  define FORSTMT(Type, Base) STMT(Type, Base)
      |                               ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:111:1: note: expanded from here
  111 | VisitForStmt
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1688:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromForStmt' requested here
 1688 | FORSTMT(ForStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1686:31: note: expanded from macro 'FORSTMT'
 1686 | #  define FORSTMT(Type, Base) STMT(Type, Base)
      |                               ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:114:1: note: expanded from here
  114 | WalkUpFromForStmt
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:251:10: note: implicitly declared private here
  251 |     bool VisitForStmt(ForStmt *FS) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1694:1: error: 'VisitDoStmt' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
 1694 | DOSTMT(DoStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1692:30: note: expanded from macro 'DOSTMT'
 1692 | #  define DOSTMT(Type, Base) STMT(Type, Base)
      |                              ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:115:1: note: expanded from here
  115 | VisitDoStmt
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1694:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromDoStmt' requested here
 1694 | DOSTMT(DoStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1692:30: note: expanded from macro 'DOSTMT'
 1692 | #  define DOSTMT(Type, Base) STMT(Type, Base)
      |                              ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:118:1: note: expanded from here
  118 | WalkUpFromDoStmt
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:246:10: note: implicitly declared private here
  246 |     bool VisitDoStmt(DoStmt *DS) {
      |          ^
In file included from /home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:8:
In file included from /home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:395:
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1706:1: error: 'VisitDeclStmt' is a private member of '(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor'
 1706 | DECLSTMT(DeclStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1704:32: note: expanded from macro 'DECLSTMT'
 1704 | #  define DECLSTMT(Type, Base) STMT(Type, Base)
      |                                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:391:12: note: expanded from macro 'STMT'
  391 |     TRY_TO(Visit##CLASS(S));                                                   \
      |            ^
<scratch space>:123:1: note: expanded from here
  123 | VisitDeclStmt
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1706:1: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::WalkUpFromDeclStmt' requested here
 1706 | DECLSTMT(DeclStmt, Stmt)
      | ^
/home/checker/llvm-build/tools/clang/include/clang/AST/StmtNodes.inc:1704:32: note: expanded from macro 'DECLSTMT'
 1704 | #  define DECLSTMT(Type, Base) STMT(Type, Base)
      |                                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:651:14: note: expanded from macro 'STMT'
  651 |       TRY_TO(WalkUpFrom##CLASS(static_cast<CLASS *>(S)));                      \
      |              ^
<scratch space>:126:1: note: expanded from here
  126 | WalkUpFromDeclStmt
      | ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:697:16: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::PostVisitStmt' requested here
  697 |         TRY_TO(PostVisitStmt(CurrS));
      |                ^
/home/llvm/llvm-project/clang/include/clang/AST/RecursiveASTVisitor.h:64:23: note: expanded from macro 'TRY_TO'
   64 |     if (!getDerived().CALL_EXPR)                                               \
      |                       ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:334:44: note: in instantiation of member function 'clang::RecursiveASTVisitor<(anonymous namespace)::GeneratedUseUncheckPointerAfterMallocChecker::Visitor>::TraverseStmt' requested here
  334 |       return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
      |                                            ^
/home/checker/code_check/result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/first_checker/negative_case_6/round_1/workspace/GeneratedUseUncheckPointerAfterMallocChecker.cpp:181:10: note: implicitly declared private here
  181 |     bool VisitDeclStmt(DeclStmt *DS) {
      |          ^
15 errors generated.

Original generation context:
{"rule_name": "use-uncheck-pointer-after-malloc", "rule_description": "The rule requires that any pointer obtained through dynamic memory allocation functions (such as malloc, calloc, or realloc) must be checked for non-null before its first use. This check must occur before the pointer is used; performing the check after use is considered a violation. Acceptable check methods include explicit or implicit null pointer comparisons like if (ptr != NULL), if (ptr), or if (!ptr). If a dynamically allocated pointer is never used, it does not violate this rule. If a pointer is reallocated, it must be checked again before any subsequent use. This rule applies equally to global and local variables. Only one warning should be reported per violating pointer variable.\nScenarios that should be reported include: using a dynamically allocated pointer directly without any null check, performing a null check only after the pointer has been used, using a global variable after dynamic allocation without a check, and using pointers from calloc or realloc without a prior check.\nCorrect scenarios include: performing a null check immediately after allocation and using the pointer only after the check passes, not using the pointer after allocation, or not using a pointer after it has been reallocated. Various forms of null pointer checks, including shorthand forms, are acceptable.", "rule_id": "gjb8114-r-1-3-8", "diagnostic": ":[[@LINE]]:9: warning: 禁止动态分配的指针变量未检查即使用", "initial_case": "#include <stdlib.h>\nvoid foo(void)\n{\n    int *pa = NULL;\n    pa = (int*) malloc(sizeof(int) * 2);\n    int *pb = (int*) malloc(sizeof(int) * 2);\n    pa[0] = 1;\n    // CHECK-MESSAGES: :[[@LINE]]:9: warning: 禁止动态分配的指针变量未检查即使用 [gjb8114-r-1-3-8]\n    pa[1] = 2;\n    pb[0] = 3;\n    // CHECK-MESSAGES: :[[@LINE]]:9: warning: 禁止动态分配的指针变量未检查即使用 [gjb8114-r-1-3-8]\n    pb[1] = 4;\n}", "extracted_logic": [{"intent": "Detect a dynamically allocated pointer being used before any null check after `malloc`, `calloc`, or `realloc` returns it.", "trigger": "A pointer variable assigned from a dynamic allocation function is dereferenced, indexed, passed to a function, or otherwise used before any prior null comparison or truthiness check on that same allocation result.", "constraints": ["The check must happen before the first use of the allocated pointer.", "Accept explicit and implicit null checks such as `ptr != NULL`, `ptr == NULL`, `if (ptr)`, and `if (!ptr)`.", "If the pointer is never used after allocation, do not warn.", "If the pointer is reallocated with `realloc`, require a fresh null check before any later use.", "Apply the rule to both local and global variables.", "Report only one warning per violating pointer variable."], "csa_api_search_terms": ["MallocChecker", "checkPostCall", "CallEvent", "RegionStore", "SVal", "ConstraintManager", "assume", "NullDereference", "checkLocation", "checkBind", "SymbolRef", "MemRegion", "VarRegion"]}, {"intent": "Detect direct use of a freshly allocated pointer without any preceding null validation.", "trigger": "Code performs an array access, field access, pointer dereference, or function call using a value originating from `malloc`/`calloc`/`realloc` before a null-check branch dominates that use.", "constraints": ["The use may appear immediately after allocation in the same block.", "The violation is based on ordering, not merely on the presence of a check somewhere later in the function.", "A later check does not repair an earlier use.", "The checker should treat `realloc` results the same as initial allocation results."], "csa_api_search_terms": ["ExprEngine", "BugReporter", "ExplodedNode", "PostStmt", "PreStmt", "BinaryOperator", "UnaryOperator", "ArraySubscriptExpr", "CStyleCastExpr", "IgnoreParenImpCasts"]}, {"intent": "Detect null checks that occur only after the allocated pointer has already been used.", "trigger": "A pointer from dynamic allocation is used first, then later guarded by an `if` or equivalent null test, with the earlier use already violating the rule.", "constraints": ["The null check must precede the first use to be valid.", "Branching after the first use does not suppress the warning.", "Multiple later checks still do not repair the earlier violation.", "Only one warning should be emitted for the variable even if it is used multiple times before the first check."], "csa_api_search_terms": ["ProgramState", "LocationContext", "ControlFlowCondition", "BranchNode", "IfStmt", "CheckerContext", "assumeDual", "DynamicTypeInfo"]}, {"intent": "Detect use of a dynamically allocated global variable before any null check.", "trigger": "A global pointer initialized or assigned from `malloc`, `calloc`, or `realloc` is later used without a prior null check on that same global value.", "constraints": ["The rule applies equally to globals and locals.", "Track assignments that happen in one function and uses that happen in another if the analysis path supports it.", "A null check must dominate the use for the relevant allocation instance.", "Only one warning per global variable violation."], "csa_api_search_terms": ["GlobalVariable", "VarRegion", "MemRegion", "StoreManager", "DeclRefExpr", "RegionStoreManager", "bindLoc", "load"]}, {"intent": "Detect use of `calloc` results without a prior null check.", "trigger": "A pointer returned from `calloc` is used before being compared against null or tested in a truthiness condition.", "constraints": ["`calloc` must be treated as a dynamic allocation source equivalent to `malloc`.", "The first use after allocation must be dominated by a null check.", "If the pointer is never used, no diagnostic should be emitted.", "Do not emit duplicate warnings for repeated uses of the same unguarded allocation."], "csa_api_search_terms": ["calloc", "MallocChecker", "CallDescription", "CallEvent", "PostCall", "AllocationState", "SymbolRef", "checkPostCall"]}, {"intent": "Detect use of `realloc` results without a fresh null check after reassignment.", "trigger": "A pointer reassigned from `realloc` is used before any new null check on the updated value.", "constraints": ["A previous check on the old value does not count for the new `realloc` result.", "The analysis must reset the checked status when `realloc` overwrites the pointer value.", "If the reallocated pointer is never used, do not warn.", "One warning per variable is enough even if multiple uses follow the missing check."], "csa_api_search_terms": ["realloc", "checkPostCall", "SymbolReaper", "StoreManager", "RegionStore", "SymbolRef", "assume", "checkDeadSymbols"]}, {"intent": "Recognize valid null-check patterns that satisfy the rule before first use.", "trigger": "The allocated pointer is tested with direct comparison or implicit boolean check before any subsequent use, and the use occurs only on the checked path.", "constraints": ["Accept `if (ptr != NULL)`, `if (ptr == NULL)`, `if (ptr)`, and `if (!ptr)` forms.", "The check must be control-flow relevant to the use.", "Checks after use do not qualify.", "The rule is about presence and ordering of the check, not a specific syntax form."], "csa_api_search_terms": ["BranchCondition", "ConditionTruthVal", "ImplicitCastExpr", "BinaryOperator", "UnaryOperator", "isNullPointerConstant", "assume", "ConstraintManager"]}, {"intent": "Suppress diagnostics when the allocated pointer is never used after allocation.", "trigger": "A pointer is returned by a dynamic allocation function and then remains unused for the rest of its lifetime in the analyzed scope.", "constraints": ["No warning should be emitted if there is no dereference, indexing, field access, call argument use, or similar consumption.", "The absence of a null check is not a violation by itself if there is no use.", "Track this behavior for both locals and globals."], "csa_api_search_terms": ["LiveVariables", "DeadSymbols", "checkDeadSymbols", "SymbolRef", "ExplodedGraph", "ProgramState", "RegionStore"]}], "retrieved_metaops": [{"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkLocation"], "kind": "detection", "meta_op": "Read RegionState on memory access and report use of a released allocation.", "behavior": {"preconditions": [], "state_reads": ["RegionState[accessed symbol]"], "state_writes": [], "transitions": [], "reports": ["Use of memory after it is freed"]}, "meta_impl": "void MallocChecker::checkLocation(SVal l, bool isLoad, const Stmt *S,\n                                  CheckerContext &C) const {\n  SymbolRef Sym = l.getLocSymbolInBase();\n  if (Sym) {\n    checkUseAfterFree(Sym, C, S);\n    checkUseZeroAllocated(Sym, C, S);\n  }\n\nvoid MallocChecker::HandleUseAfterFree(CheckerContext &C, SourceRange Range,\n                                       SymbolRef Sym) const {\n  const UseFree *Frontend = getRelevantFrontendAs<UseFree>(C, Sym);\n  if (!Frontend)\n    return;\n  if (!Frontend->isEnabled()) {\n    C.addSink();\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkLocation", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3668, "end_line": 3674}, {"role": "report_helper", "symbol": "MallocChecker::HandleUseAfterFree", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2798, "end_line": 2806}], "api_refs": [{"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}, {"id": "api:8914c5ed6dc0f00387b69627", "qualified_name": "clang::ento::CheckerContext::emitReport"}], "depends_on": ["metaop:755cd4eed00d6aa938b1493d"], "_embedding_id": "metaop:0c42cf4c9057aa4b060de371", "_similarity": 0.7672107815742493, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "state_transition", "meta_op": "Validate a deallocation and mark the released symbol in RegionState.", "behavior": {"preconditions": [], "state_reads": ["RegionState[released symbol]"], "state_writes": ["RegionState[released symbol] = released"], "transitions": [], "reports": []}, "meta_impl": "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr,\n                          const CallEvent &Call, ProgramStateRef State,\n                          bool Hold, bool &IsKnownToBeAllocated,\n                          AllocationFamily Family, bool ReturnsNullOnFailure,\n                          std::optional<SVal> ArgValOpt) const {\n\n  if (!State)\n    return nullptr;\n\n  SVal ArgVal = ArgValOpt.value_or(C.getSVal(ArgExpr));\n  if (!isa<DefinedOrUnknownSVal>(ArgVal))\n    return nullptr;\n  DefinedOrUnknownSVal location = ArgVal.castAs<DefinedOrUnknownSVal>();\n\n  // Check for null dereferences.\n  if (!isa<Loc>(location))\n    return nullptr;\n\n  // The explicit NULL case, no operation is performed.\n  ProgramStateRef notNullState, nullState;\n  std::tie(notNullState, nullState) = State->assume(location);\n  if (nullState && !notNullState)\n    return nullptr;\n\n  // Unknown values could easily be okay\n  // Undefined values are handled elsewhere\n  if (ArgVal.isUnknownOrUndef())\n    return nullptr;\n\n  const MemRegion *R = ArgVal.getAsRegion();\n  const Expr *ParentExpr = Call.getOriginExpr();\n\n  // NOTE: We detected a bug, but the checker under whose name we would emit the\n  // error c", "source_spans": [{"role": "helper", "symbol": "MallocChecker::FreeMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2315, "end_line": 2974}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}], "depends_on": ["metaop:97f65925f14ff701701ae673"], "_embedding_id": "metaop:755cd4eed00d6aa938b1493d", "_similarity": 0.7670662999153137, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "entry_filter", "meta_op": "Dispatch recognized deallocation and allocation calls to checker-local models.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": [], "transitions": [], "reports": []}, "meta_impl": "void MallocChecker::checkPreCall(const CallEvent &Call,\n                                 CheckerContext &C) const {\n\n  if (const auto *DC = dyn_cast<CXXDeallocatorCall>(&Call)) {\n    const CXXDeleteExpr *DE = DC->getOriginExpr();\n\n    // FIXME: I don't see a good reason for restricting the check against\n    // use-after-free violations to the case when NewDeleteChecker is disabled.\n    // (However, if NewDeleteChecker is enabled, perhaps it would be better to\n    // do this check a bit later?)\n    if (!NewDeleteChecker.isEnabled())\n      if (SymbolRef Sym = C.getSVal(DE->getArgument()).getAsSymbol())\n        checkUseAfterFree(Sym, C, DE->getArgument());\n\n    if (!isStandardNewDelete(DC->getDecl()))\n      return;\n\n    ProgramStateRef State = C.getState();\n    bool IsKnownToBeAllocated;\n    State = FreeMemAux(\n        C, DE->getArgument(), Call, State,\n        /*Hold*/ false, IsKnownToBeAllocated,\n        AllocationFamily(DE->isArrayForm() ? AF_CXXNewArray : AF_CXXNew));\n\n    C.addTransition(State);\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkPreCall", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3445, "end_line": 3471}], "api_refs": [], "depends_on": [], "_embedding_id": "metaop:97f65925f14ff701701ae673", "_similarity": 0.75016188621521, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}], "callbacks": ["MallocChecker::checkDeadSymbols"], "kind": "lifecycle_cleanup", "meta_op": "Collect allocated dead symbols as leaks and remove dead allocation state.", "behavior": {"preconditions": [], "state_reads": ["RegionState entries"], "state_writes": ["remove dead allocation state"], "transitions": [], "reports": ["memory leak"]}, "meta_impl": "void MallocChecker::checkDeadSymbols(SymbolReaper &SymReaper,\n                                     CheckerContext &C) const\n{\n  ProgramStateRef state = C.getState();\n  RegionStateTy OldRS = state->get<RegionState>();\n  RegionStateTy::Factory &F = state->get_context<RegionState>();\n\n  RegionStateTy RS = OldRS;\n  SmallVector<SymbolRef, 2> Errors;\n  for (auto [Sym, State] : RS) {\n    if (SymReaper.isDead(Sym)) {\n      if (State.isAllocated() || State.isAllocatedOfSizeZero())\n        Errors.push_back(Sym);\n      // Remove the dead symbol from the map.\n      RS = F.remove(RS, Sym);\n    }\n  }\n\n  if (RS == OldRS) {\n    // We shouldn't have touched other maps yet.\n    assert(state->get<ReallocPairs>() ==\n           C.getState()->get<ReallocPairs>());\n    assert(state->get<FreeReturnValue>() ==\n           C.getState()->get<FreeReturnValue>());\n    return;\n  }\n\n  // Cleanup the Realloc Pairs Map.\n  ReallocPairsTy RP = state->get<ReallocPairs>();\n  for (auto [Sym, ReallocPair] : RP) {\n    if (SymReaper.isDead(Sym) || SymReaper.isDead(ReallocPair.ReallocatedSym)) {\n      state = state->remove<ReallocPairs>(Sym);\n    }\n  }\n\n  // Cleanup the FreeReturnValue Map.\n  FreeReturnValueTy FR = state->g", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkDeadSymbols", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3132, "end_line": 3469}], "api_refs": [{"id": "api:432eb5b9ff50440a0794eb99", "qualified_name": "clang::ento::SymbolReaper::isDead"}, {"id": "api:4db73b63e0c13374bd4f2d68", "qualified_name": "clang::ento::ProgramState::remove"}, {"id": "api:2669ca957a0ccf39ad92c422", "qualified_name": "clang::ento::CheckerContext::addTransition"}], "depends_on": ["metaop:ab94c1766baa204d15b85804"], "_embedding_id": "metaop:72d54c7d67e9a0cbaf78dcc9", "_similarity": 0.74986732006073, "_retrieval": "embedding"}], "retrieved_api_refs": [{"id": "type:17b2d89e5795205a2881eaf9", "kind": "struct", "name": "ImplicitNullDerefEvent", "qualified_name": "clang::ento::ImplicitNullDerefEvent", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "We dereferenced a location that may be null.", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 624, "end_line": 635, "code": "struct ImplicitNullDerefEvent {\n  SVal Location;\n  bool IsLoad;\n  ExplodedNode *SinkNode;\n  BugReporter *BR;\n  // When true, the dereference is in the source code directly. When false, the\n  // dereference might happen later (for example pointer passed to a parameter\n  // that is marked with nonnull attribute.)\n  bool IsDirectDereference;\n\n  static int Tag;\n}"}, "_embedding_id": "type:17b2d89e5795205a2881eaf9", "_similarity": 0.6847270727157593, "_retrieval": "embedding"}, {"id": "api:5c92afa46cac3694d3ded65e", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::StoreManager::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:d8f2754cb4d89590df1399f1", "owner_name": "clang::ento::StoreManager", "signature": "virtual StoreRef invalidateRegions( Store store, ArrayRef<SVal> Values, ConstCFGElementRef Elem, unsigned Count, const StackFrame *SF, const CallEvent *Call, InvalidatedSymbols &IS, RegionAndSymbolInvalidationTraits &ITraits, InvalidatedRegions *TopLevelRegions, InvalidatedRegions *Invalidated) = 0", "return_type": "StoreRef", "parameters": [{"position": 0, "name": "store", "type": "Store", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Values", "type": "ArrayRef<SVal>", "canonical_type": null, "default_value": null}, {"position": 2, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Count", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 4, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 5, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": null}, {"position": 6, "name": "IS", "type": "InvalidatedSymbols &", "canonical_type": null, "default_value": null}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits &", "canonical_type": null, "default_value": null}, {"position": 8, "name": "TopLevelRegions", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}, {"position": 9, "name": "Invalidated", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": true, "pure_virtual": true, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "invalidateRegions - Clears out the specified regions from the store,\n marking their values as unknown. Depending on the store, this may also\n invalidate additional regions that may have changed based on accessing\n the given regions. If \\p Call is non-null, then this also invalidates\n non-static globals (but if \\p Call is from a system header, then this is\n limited to globals declared in system headers).\n\nInstead of calling this method directly, you should probably use\n\\c ProgramState::invalidateRegions, which calls this and then ensures that\nthe relevant checker callbacks are triggered.\n\n\\param[in] store The initial store.\n\\param[in] Values The values to invalidate.\n\\param[in] Elem The current CFG Element being evaluated. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Count The current block count. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Call The call expression which will be used to determine which\n  globals should get invalidated.\n\\param[in,out] IS A set to fill with any symbols that are no longer\n  accessible. Pass \\c NULL if this information will not be used.\n\\param[in] ITraits Information about invalidati", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/Store.h"], "_embedding_id": "api:5c92afa46cac3694d3ded65e", "_similarity": 0.6758955717086792, "_retrieval": "embedding"}, {"id": "api:4162d561535c52fa34f481ba", "kind": "method", "name": "getCapturedRegion", "qualified_name": "clang::ento::BlockDataRegion::getCapturedRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:4162d561535c52fa34f481ba", "_similarity": 0.6695581674575806, "_retrieval": "embedding"}, {"id": "api:b45c2d2855b70b4ff2043dc1", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::ProgramState::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef invalidateRegions( ArrayRef<const MemRegion *> Regions, ConstCFGElementRef Elem, unsigned BlockCount, const StackFrame *SF, bool CausesPointerEscape, InvalidatedSymbols *IS = nullptr, const CallEvent *Call = nullptr, RegionAndSymbolInvalidationTraits *ITraits = nullptr) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "Regions", "type": "ArrayRef<const MemRegion *>", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 2, "name": "BlockCount", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 3, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 4, "name": "CausesPointerEscape", "type": "bool", "canonical_type": null, "default_value": null}, {"position": 5, "name": "IS", "type": "InvalidatedSymbols *", "canonical_type": null, "default_value": "nullptr"}, {"position": 6, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": "nullptr"}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns the state with bindings for the given regions cleared from the\nstore. If \\p Call is non-null, also invalidates global regions (but if\n\\p Call is from a system header, then this is limited to globals declared\nin system headers).\n\nThis calls the lower-level method \\c StoreManager::invalidateRegions to\ndo the actual invalidation, then calls the checker callbacks which should\nbe triggered by this event.\n\n\\param Regions the set of regions to be invalidated.\n\\param Elem The CFG Element that caused the invalidation.\n\\param BlockCount The number of times the current basic block has been\n       visited.\n\\param CausesPointerEscape the flag is set to true when the invalidation\n       entails escape of a symbol (representing a pointer). For example,\n       due to it being passed as an argument in a call.\n\\param IS the set of invalidated symbols.\n\\param Call if non-null, the invalidated regions represent parameters to\n       the call and should be considered directly invalidated.\n\\param ITraits information about special handling for particular regions\n       or symbols.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:b45c2d2855b70b4ff2043dc1", "_similarity": 0.6629656553268433, "_retrieval": "embedding"}, {"id": "api:75cddbf011a870947e600b61", "kind": "method", "name": "bindDefaultInitial", "qualified_name": "clang::ento::ProgramState::bindDefaultInitial", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef bindDefaultInitial(SVal loc, SVal V, const StackFrame *SF) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "loc", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 1, "name": "V", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 2, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Initializes the region of memory represented by \\p loc with an initial\nvalue. Once initialized, all values loaded from any sub-regions of that\nregion will be equal to \\p V, unless overwritten later by the program.\nThis method should not be used on regions that are already initialized.\nIf you need to indicate that memory contents have suddenly become unknown\nwithin a certain region of memory, consider invalidateRegions().", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:75cddbf011a870947e600b61", "_similarity": 0.6611728668212891, "_retrieval": "embedding"}, {"id": "api:75a14f374e5263695cdb535a", "kind": "method", "name": "getRegion", "qualified_name": "clang::ento::nonloc::LazyCompoundVal::getRegion", "namespace": "clang::ento::nonloc", "owner_id": "type:8d160636bf8e70eabdceae17", "owner_name": "clang::ento::nonloc::LazyCompoundVal", "signature": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *getRegion() const", "return_type": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "This function itself is immaterial. It is only an implementation detail.\nLazyCompoundVal represents only the rvalue, the data (known or unknown)\nthat *was* stored in that region *at some point in the past*. The region\nshould not be used for any purpose other than figuring out what part of\nthe frozen Store you're interested in. The value does not represent the\ncurrent* value of that region. Sometimes it may, but this should not be\nrelied upon. Instead, if you want to figure out what region it represents,\nyou typically need to see where you got it from in the first place. The\nregion is absolutely not analogous to the C++ \"this\" pointer. It is also\nnot a valid way to \"materialize\" the prvalue into a glvalue in C++,\nbecause the region represents the *old* storage (sometimes very old), not\nthe *future* storage.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SVals.h"], "_embedding_id": "api:75a14f374e5263695cdb535a", "_similarity": 0.661008358001709, "_retrieval": "embedding"}, {"id": "api:07f9154ceaf117fd3a90a68a", "kind": "method", "name": "getOriginalRegion", "qualified_name": "clang::ento::BlockDataRegion::getOriginalRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:07f9154ceaf117fd3a90a68a", "_similarity": 0.6609539985656738, "_retrieval": "embedding"}, {"id": "api:59a9120121473d39ba2a4401", "kind": "method", "name": "getSValAsScalarOrLoc", "qualified_name": "clang::ento::ProgramState::getSValAsScalarOrLoc", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "SVal getSValAsScalarOrLoc(const MemRegion *R) const", "return_type": "SVal", "parameters": [{"position": 0, "name": "R", "type": "const MemRegion *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Return the value bound to the specified location, assuming\nthat the value is a scalar integer or an enumeration or a pointer.\nReturns UnknownVal() if none found or the region is not known to hold\na value of such type.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:59a9120121473d39ba2a4401", "_similarity": 0.658152163028717, "_retrieval": "embedding"}, {"id": "api:bb5d1fac98d62b06da1c9530", "kind": "method", "name": "addTransition", "qualified_name": "clang::ento::CheckerContext::addTransition", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "ExplodedNode *addTransition(ProgramStateRef State = nullptr, const ProgramPointTag *Tag = nullptr)", "return_type": "ExplodedNode *", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": "nullptr"}, {"position": 1, "name": "Tag", "type": "const ProgramPointTag *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Generates a new transition in the program state graph\n(ExplodedGraph). Uses the default CheckerContext predecessor node.\n\n@param State The state of the generated node. If not specified, the state\n       will not be changed, but the new node will have the checker's tag.\n@param Tag The tag is used to uniquely identify the creation site. If no\n       tag is specified, a default tag, unique to the given checker,\n       will be used. Tags are used to prevent states generated at\n       different sites from caching out.\nNOTE: If the State is unchanged and the Tag is nullptr, this may return a\nnode which is not tagged (instead of using the default tag corresponding\nto the active checker). This is arguably a bug and should be fixed.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 193, "end_line": 196, "code": "ExplodedNode *addTransition(ProgramStateRef State = nullptr,\n                              const ProgramPointTag *Tag = nullptr) {\n    return addTransitionImpl(State ? State : getState(), false, nullptr, Tag);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:8914c5ed6dc0f00387b69627", "kind": "method", "name": "emitReport", "qualified_name": "clang::ento::CheckerContext::emitReport", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "void emitReport(std::unique_ptr<BugReport> R)", "return_type": "void", "parameters": [{"position": 0, "name": "R", "type": "std::unique_ptr<BugReport>", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Emit the diagnostics report.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 288, "end_line": 291, "code": "void emitReport(std::unique_ptr<BugReport> R) {\n    Changed = true;\n    Eng.getBugReporter().emitReport(std::move(R));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "kind": "method", "name": "get", "qualified_name": "clang::ento::ProgramState::get", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> typename ProgramStateTrait<T>::data_type get() const", "return_type": "typename ProgramStateTrait<T>::data_type", "parameters": [], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 427, "end_line": 431, "code": "template <typename T>\n  typename ProgramStateTrait<T>::data_type\n  get() const {\n    return ProgramStateTrait<T>::MakeData(FindGDM(ProgramStateTrait<T>::GDMIndex()));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:a632ec38e93b776dc3ad7723", "kind": "method", "name": "remove", "qualified_name": "clang::ento::ProgramState::remove", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef remove(typename ProgramStateTrait<T>::key_type K) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "K", "type": "typename ProgramStateTrait<T>::key_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 828, "end_line": 831, "code": "template<typename T>\nProgramStateRef ProgramState::remove(typename ProgramStateTrait<T>::key_type K) const {\n  return getStateManager().remove<T>(this, K, get_context<T>());\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:27be6c71f8737ec8709572f6", "kind": "method", "name": "set", "qualified_name": "clang::ento::ProgramState::set", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef set(typename ProgramStateTrait<T>::data_type D) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "D", "type": "typename ProgramStateTrait<T>::data_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 844, "end_line": 847, "code": "template<typename T>\nProgramStateRef ProgramState::set(typename ProgramStateTrait<T>::data_type D) const {\n  return getStateManager().set<T>(this, D);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:432eb5b9ff50440a0794eb99", "kind": "method", "name": "isDead", "qualified_name": "clang::ento::SymbolReaper::isDead", "namespace": "clang::ento", "owner_id": "type:0f638a5e3926be17bca4229e", "owner_name": "clang::ento::SymbolReaper", "signature": "bool isDead(SymbolRef sym)", "return_type": "bool", "parameters": [{"position": 0, "name": "sym", "type": "SymbolRef", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns whether or not a symbol has been confirmed dead.\n\nThis should only be called once all marking of dead symbols has completed.\n(For checkers, this means only in the checkDeadSymbols callback.)", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/SymbolManager.h", "start_line": 629, "end_line": 631, "code": "bool isDead(SymbolRef sym) {\n    return !isLive(sym);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SymbolManager.h"], "_retrieval": "metaop_api_ref"}, {"id": "type:9dd6ea9e6fc40f462913fff1", "kind": "class", "name": "ASTCodeBody", "qualified_name": "clang::ento::check::ASTCodeBody", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 48, "end_line": 61, "code": "class ASTCodeBody {\n  template <typename CHECKER>\n  static void _checkBody(void *checker, const Decl *D, AnalysisManager& mgr,\n                         BugReporter &BR) {\n    ((const CHECKER *)checker)->checkASTCodeBody(D, mgr, BR);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBody(CheckerManager::CheckDeclFunc(checker,\n                                                       _checkBody<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}, {"id": "type:0cd555dadc4121b45bcf8014", "kind": "class", "name": "BranchCondition", "qualified_name": "clang::ento::check::BranchCondition", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 299, "end_line": 313, "code": "class BranchCondition {\n  template <typename CHECKER>\n  static void _checkBranchCondition(void *checker, const Stmt *Condition,\n                                    CheckerContext & C) {\n    ((const CHECKER *)checker)->checkBranchCondition(Condition, C);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBranchCondition(\n      CheckerManager::CheckBranchConditionFunc(checker,\n                                               _checkBranchCondition<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}]}
Implementation:
#include <memory>
#include <string>
#include <unordered_map>

#include "clang/AST/Decl.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/StaticAnalyzer/Core/AnalyzerOptions.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugReporter.h"
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/Checker.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/AnalysisManager.h"
#include "clang/StaticAnalyzer/Frontend/CheckerRegistry.h"

using namespace clang;
using namespace ento;

namespace {

class GeneratedUseUncheckPointerAfterMallocChecker
    : public Checker<check::ASTCodeBody> {
  const BugType BT{this, "Generated GJB8114 violation", "GJB8114"};

  struct PtrInfo {
    const VarDecl *VD = nullptr;
    bool Allocated = false;
    bool Checked = false;
    bool Used = false;
    bool Reported = false;
    SourceLocation FirstUseLoc;
  };

  class Visitor : public RecursiveASTVisitor<Visitor> {
    GeneratedUseUncheckPointerAfterMallocChecker &Checker;
    AnalysisDeclContext *ADC;
    BugReporter &BR;
    SourceManager &SM;
    std::unordered_map<const VarDecl *, PtrInfo> Infos;
    std::unordered_map<std::string, const VarDecl *> GlobalsByName;

    static const VarDecl *getTargetVar(const Expr *E) {
      E = E ? E->IgnoreParenImpCasts() : nullptr;
      if (!E)
        return nullptr;

      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());

      if (const auto *ME = dyn_cast<MemberExpr>(E))
        return dyn_cast<VarDecl>(ME->getMemberDecl());

      return nullptr;
    }

    static const Expr *strip(const Expr *E) {
      return E ? E->IgnoreParenImpCasts() : nullptr;
    }

    static bool isNullLiteral(const Expr *E) {
      E = strip(E);
      return E && isa<CXXNullPtrLiteralExpr>(E);
    }

    static bool isAllocCall(const CallExpr *CE) {
      const FunctionDecl *FD = CE ? CE->getDirectCallee() : nullptr;
      if (!FD)
        return false;
      IdentifierInfo *II = FD->getIdentifier();
      if (!II)
        return false;
      StringRef Name = II->getName();
      return Name == "malloc" || Name == "calloc" || Name == "realloc";
    }

    static bool isAssignmentToVar(const Stmt *S, const VarDecl *VD,
                                  const Expr *&RHS) {
      const auto *BO = dyn_cast_or_null<BinaryOperator>(S);
      if (!BO || !BO->isAssignmentOp())
        return false;
      if (getTargetVar(BO->getLHS()) != VD)
        return false;
      RHS = BO->getRHS();
      return true;
    }

    static const VarDecl *getReferencedVar(const Expr *E) {
      E = strip(E);
      if (!E)
        return nullptr;
      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl());
      return nullptr;
    }

    bool exprUsesTrackedPtr(const Expr *E, const VarDecl *VD) const {
      if (!E)
        return false;
      E = E->IgnoreParenImpCasts();

      if (const auto *DRE = dyn_cast<DeclRefExpr>(E))
        return dyn_cast<VarDecl>(DRE->getDecl()) == VD;

      if (const auto *UO = dyn_cast<UnaryOperator>(E))
        return exprUsesTrackedPtr(UO->getSubExpr(), VD);

      for (const Stmt *Child : E->children()) {
        if (const auto *CE = dyn_cast_or_null<Expr>(Child))
          if (exprUsesTrackedPtr(CE, VD))
            return true;
      }
      return false;
    }

    void markChecked(const VarDecl *VD) {
      auto &Info = Infos[VD];
      Info.VD = VD;
      Info.Checked = true;
    }

    void noteUse(const VarDecl *VD, const Expr *UseExpr) {
      auto &Info = Infos[VD];
      Info.VD = VD;
      if (Info.Allocated && !Info.Checked && !Info.Reported) {
        Info.Used = true;
        Info.FirstUseLoc = UseExpr->getBeginLoc();
      }
    }

    void reportIfNeeded(const VarDecl *VD, const Expr *UseExpr) {
      auto &Info = Infos[VD];
      if (!Info.Allocated || Info.Checked || Info.Reported)
        return;

      SourceLocation Loc = UseExpr->getBeginLoc();
      if (Loc.isInvalid())
        Loc = Info.FirstUseLoc.isValid() ? Info.FirstUseLoc : VD->getLocation();

      PathDiagnosticLocation PDL(Loc, SM);
      auto Report = std::make_unique<BasicBugReport>(
          Checker.BT, "禁止动态分配的指针变量未检查即使用", PDL);
      Report->addRange(UseExpr->getSourceRange());
      Report->addRange(VD->getSourceRange());
      Report->setDeclWithIssue(ADC->getDecl());
      BR.emitReport(std::move(Report));
      Info.Reported = true;
    }

    void scanConditionForCheck(const Expr *Cond) {
      Cond = strip(Cond);
      if (!Cond)
        return;

      if (const auto *UO = dyn_cast<UnaryOperator>(Cond)) {
        if (UO->getOpcode() == UO_LNot) {
          if (const VarDecl *VD = getReferencedVar(UO->getSubExpr()))
            markChecked(VD);
        }
      }

      if (const auto *BO = dyn_cast<BinaryOperator>(Cond)) {
        if (BO->isRelationalOp() || BO->isEqualityOp()) {
          const VarDecl *L = getReferencedVar(BO->getLHS());
          const VarDecl *R = getReferencedVar(BO->getRHS());
          if ((L && isNullLiteral(BO->getRHS())) ||
              (R && isNullLiteral(BO->getLHS())) || L || R) {
            if (L)
              markChecked(L);
            if (R)
              markChecked(R);
          }
        }
      }

      if (const auto *DRE = dyn_cast<DeclRefExpr>(Cond)) {
        if (const auto *VD = dyn_cast<VarDecl>(DRE->getDecl()))
          markChecked(VD);
      }
    }

    bool VisitDeclStmt(DeclStmt *DS) {
      for (Decl *D : DS->decls()) {
        const auto *VD = dyn_cast<VarDecl>(D);
        if (!VD)
          continue;
        if (VD->hasGlobalStorage())
          GlobalsByName[VD->getNameAsString()] = VD;

        const Expr *Init = VD->getInit();
        if (const auto *CE = dyn_cast_or_null<CallExpr>(Init)) {
          if (isAllocCall(CE)) {
            auto &Info = Infos[VD];
            Info.VD = VD;
            Info.Allocated = true;
            Info.Checked = false;
            Info.Used = false;
            Info.Reported = false;
          }
        }
      }
      return true;
    }

    bool VisitBinaryOperator(BinaryOperator *BO) {
      if (!BO->isAssignmentOp())
        return true;

      const Expr *RHS = nullptr;
      const VarDecl *LHSVar = nullptr;
      if (const auto *LHS = strip(BO->getLHS()))
        LHSVar = getTargetVar(LHS);

      if (!LHSVar)
        return true;

      RHS = BO->getRHS();
      if (const auto *CE = dyn_cast_or_null<CallExpr>(strip(RHS))) {
        if (isAllocCall(CE)) {
          auto &Info = Infos[LHSVar];
          Info.VD = LHSVar;
          Info.Allocated = true;
          Info.Checked = false;
          Info.Used = false;
          Info.Reported = false;
          return true;
        }
      }

      if (exprUsesTrackedPtr(RHS, LHSVar)) {
        noteUse(LHSVar, BO);
        reportIfNeeded(LHSVar, BO);
      }
      return true;
    }

    bool VisitIfStmt(IfStmt *IS) {
      scanConditionForCheck(IS->getCond());
      return true;
    }

    bool VisitWhileStmt(WhileStmt *WS) {
      scanConditionForCheck(WS->getCond());
      return true;
    }

    bool VisitDoStmt(DoStmt *DS) {
      scanConditionForCheck(DS->getCond());
      return true;
    }

    bool VisitForStmt(ForStmt *FS) {
      if (FS->getCond())
        scanConditionForCheck(FS->getCond());
      return true;
    }

    bool VisitUnaryOperator(UnaryOperator *UO) {
      if (!(UO->isIncrementDecrementOp() || UO->getOpcode() == UO_Deref))
        return true;

      const VarDecl *VD = getReferencedVar(UO->getSubExpr());
      if (!VD)
        return true;

      auto It = Infos.find(VD);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(VD, UO);
      reportIfNeeded(VD, UO);
      return true;
    }

    bool VisitArraySubscriptExpr(ArraySubscriptExpr *ASE) {
      const VarDecl *Base = getReferencedVar(ASE->getBase());
      if (!Base)
        return true;

      auto It = Infos.find(Base);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(Base, ASE);
      reportIfNeeded(Base, ASE);
      return true;
    }

    bool VisitMemberExpr(MemberExpr *ME) {
      const VarDecl *Base = getReferencedVar(ME->getBase());
      if (!Base)
        return true;

      auto It = Infos.find(Base);
      if (It == Infos.end() || !It->second.Allocated)
        return true;

      noteUse(Base, ME);
      reportIfNeeded(Base, ME);
      return true;
    }

  public:
    Visitor(GeneratedUseUncheckPointerAfterMallocChecker &Checker,
            AnalysisDeclContext *ADC, BugReporter &BR)
        : Checker(Checker), ADC(ADC), BR(BR),
          SM(BR.getSourceManager()) {}

    bool VisitCallExpr(CallExpr *CE) {
      if (!CE)
        return true;

      if (isAllocCall(CE)) {
        if (const Expr *Parent = dyn_cast_or_null<Expr>(CE->getStmtClass() ?
                                                        nullptr : nullptr)) {
          (void)Parent;
        }
        return true;
      }

      for (const Expr *Arg : CE->arguments()) {
        const VarDecl *VD = getReferencedVar(Arg);
        if (!VD)
          continue;
        auto It = Infos.find(VD);
        if (It == Infos.end() || !It->second.Allocated)
          continue;
        noteUse(VD, CE);
        reportIfNeeded(VD, CE);
      }
      return true;
    }

    bool TraverseStmt(Stmt *S) {
      return RecursiveASTVisitor<Visitor>::TraverseStmt(S);
    }

    const std::unordered_map<const VarDecl *, PtrInfo> &getInfos() const {
      return Infos;
    }
  };

public:
  void checkASTCodeBody(const Decl *D, AnalysisManager &AM,
                        BugReporter &BR) const {
    const auto *FD = dyn_cast<FunctionDecl>(D);
    if (!FD || !FD->hasBody())
      return;

    AnalysisDeclContext *ADC = AM.getAnalysisDeclContext(FD);
    if (!ADC)
      return;

    Visitor V(const_cast<GeneratedUseUncheckPointerAfterMallocChecker &>(*this),
              ADC, BR);
    V.TraverseStmt(FD->getBody());
  }
};

} // namespace

extern "C" void clang_registerCheckers(CheckerRegistry &Registry) {
  Registry.addChecker<GeneratedUseUncheckPointerAfterMallocChecker>(
      "gjb8114.UseUncheckPointerAfterMalloc",
      "Generated checker for unchecked use of malloc-family pointers");
}

extern "C" const char clang_analyzerAPIVersionString[] =
    CLANG_ANALYZER_API_VERSION_STRING;
Known APIs:
[{"id": "type:17b2d89e5795205a2881eaf9", "kind": "struct", "name": "ImplicitNullDerefEvent", "qualified_name": "clang::ento::ImplicitNullDerefEvent", "namespace": "clang::ento", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "We dereferenced a location that may be null.", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 624, "end_line": 635, "code": "struct ImplicitNullDerefEvent {\n  SVal Location;\n  bool IsLoad;\n  ExplodedNode *SinkNode;\n  BugReporter *BR;\n  // When true, the dereference is in the source code directly. When false, the\n  // dereference might happen later (for example pointer passed to a parameter\n  // that is marked with nonnull attribute.)\n  bool IsDirectDereference;\n\n  static int Tag;\n}"}, "_embedding_id": "type:17b2d89e5795205a2881eaf9", "_similarity": 0.6847270727157593, "_retrieval": "embedding"}, {"id": "api:5c92afa46cac3694d3ded65e", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::StoreManager::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:d8f2754cb4d89590df1399f1", "owner_name": "clang::ento::StoreManager", "signature": "virtual StoreRef invalidateRegions( Store store, ArrayRef<SVal> Values, ConstCFGElementRef Elem, unsigned Count, const StackFrame *SF, const CallEvent *Call, InvalidatedSymbols &IS, RegionAndSymbolInvalidationTraits &ITraits, InvalidatedRegions *TopLevelRegions, InvalidatedRegions *Invalidated) = 0", "return_type": "StoreRef", "parameters": [{"position": 0, "name": "store", "type": "Store", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Values", "type": "ArrayRef<SVal>", "canonical_type": null, "default_value": null}, {"position": 2, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 3, "name": "Count", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 4, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 5, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": null}, {"position": 6, "name": "IS", "type": "InvalidatedSymbols &", "canonical_type": null, "default_value": null}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits &", "canonical_type": null, "default_value": null}, {"position": 8, "name": "TopLevelRegions", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}, {"position": 9, "name": "Invalidated", "type": "InvalidatedRegions *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": true, "pure_virtual": true, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "invalidateRegions - Clears out the specified regions from the store,\n marking their values as unknown. Depending on the store, this may also\n invalidate additional regions that may have changed based on accessing\n the given regions. If \\p Call is non-null, then this also invalidates\n non-static globals (but if \\p Call is from a system header, then this is\n limited to globals declared in system headers).\n\nInstead of calling this method directly, you should probably use\n\\c ProgramState::invalidateRegions, which calls this and then ensures that\nthe relevant checker callbacks are triggered.\n\n\\param[in] store The initial store.\n\\param[in] Values The values to invalidate.\n\\param[in] Elem The current CFG Element being evaluated. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Count The current block count. Used to conjure\n  symbols to mark the values of invalidated regions.\n\\param[in] Call The call expression which will be used to determine which\n  globals should get invalidated.\n\\param[in,out] IS A set to fill with any symbols that are no longer\n  accessible. Pass \\c NULL if this information will not be used.\n\\param[in] ITraits Information about invalidati", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/Store.h"], "_embedding_id": "api:5c92afa46cac3694d3ded65e", "_similarity": 0.6758955717086792, "_retrieval": "embedding"}, {"id": "api:4162d561535c52fa34f481ba", "kind": "method", "name": "getCapturedRegion", "qualified_name": "clang::ento::BlockDataRegion::getCapturedRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:4162d561535c52fa34f481ba", "_similarity": 0.6695581674575806, "_retrieval": "embedding"}, {"id": "api:b45c2d2855b70b4ff2043dc1", "kind": "method", "name": "invalidateRegions", "qualified_name": "clang::ento::ProgramState::invalidateRegions", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef invalidateRegions( ArrayRef<const MemRegion *> Regions, ConstCFGElementRef Elem, unsigned BlockCount, const StackFrame *SF, bool CausesPointerEscape, InvalidatedSymbols *IS = nullptr, const CallEvent *Call = nullptr, RegionAndSymbolInvalidationTraits *ITraits = nullptr) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "Regions", "type": "ArrayRef<const MemRegion *>", "canonical_type": null, "default_value": null}, {"position": 1, "name": "Elem", "type": "ConstCFGElementRef", "canonical_type": null, "default_value": null}, {"position": 2, "name": "BlockCount", "type": "unsigned", "canonical_type": null, "default_value": null}, {"position": 3, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}, {"position": 4, "name": "CausesPointerEscape", "type": "bool", "canonical_type": null, "default_value": null}, {"position": 5, "name": "IS", "type": "InvalidatedSymbols *", "canonical_type": null, "default_value": "nullptr"}, {"position": 6, "name": "Call", "type": "const CallEvent *", "canonical_type": null, "default_value": "nullptr"}, {"position": 7, "name": "ITraits", "type": "RegionAndSymbolInvalidationTraits *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns the state with bindings for the given regions cleared from the\nstore. If \\p Call is non-null, also invalidates global regions (but if\n\\p Call is from a system header, then this is limited to globals declared\nin system headers).\n\nThis calls the lower-level method \\c StoreManager::invalidateRegions to\ndo the actual invalidation, then calls the checker callbacks which should\nbe triggered by this event.\n\n\\param Regions the set of regions to be invalidated.\n\\param Elem The CFG Element that caused the invalidation.\n\\param BlockCount The number of times the current basic block has been\n       visited.\n\\param CausesPointerEscape the flag is set to true when the invalidation\n       entails escape of a symbol (representing a pointer). For example,\n       due to it being passed as an argument in a call.\n\\param IS the set of invalidated symbols.\n\\param Call if non-null, the invalidated regions represent parameters to\n       the call and should be considered directly invalidated.\n\\param ITraits information about special handling for particular regions\n       or symbols.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:b45c2d2855b70b4ff2043dc1", "_similarity": 0.6629656553268433, "_retrieval": "embedding"}, {"id": "api:75cddbf011a870947e600b61", "kind": "method", "name": "bindDefaultInitial", "qualified_name": "clang::ento::ProgramState::bindDefaultInitial", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "[[nodiscard]] ProgramStateRef bindDefaultInitial(SVal loc, SVal V, const StackFrame *SF) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "loc", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 1, "name": "V", "type": "SVal", "canonical_type": null, "default_value": null}, {"position": 2, "name": "SF", "type": "const StackFrame *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Initializes the region of memory represented by \\p loc with an initial\nvalue. Once initialized, all values loaded from any sub-regions of that\nregion will be equal to \\p V, unless overwritten later by the program.\nThis method should not be used on regions that are already initialized.\nIf you need to indicate that memory contents have suddenly become unknown\nwithin a certain region of memory, consider invalidateRegions().", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:75cddbf011a870947e600b61", "_similarity": 0.6611728668212891, "_retrieval": "embedding"}, {"id": "api:75a14f374e5263695cdb535a", "kind": "method", "name": "getRegion", "qualified_name": "clang::ento::nonloc::LazyCompoundVal::getRegion", "namespace": "clang::ento::nonloc", "owner_id": "type:8d160636bf8e70eabdceae17", "owner_name": "clang::ento::nonloc::LazyCompoundVal", "signature": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *getRegion() const", "return_type": "LLVM_ATTRIBUTE_RETURNS_NONNULL const TypedValueRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "This function itself is immaterial. It is only an implementation detail.\nLazyCompoundVal represents only the rvalue, the data (known or unknown)\nthat *was* stored in that region *at some point in the past*. The region\nshould not be used for any purpose other than figuring out what part of\nthe frozen Store you're interested in. The value does not represent the\ncurrent* value of that region. Sometimes it may, but this should not be\nrelied upon. Instead, if you want to figure out what region it represents,\nyou typically need to see where you got it from in the first place. The\nregion is absolutely not analogous to the C++ \"this\" pointer. It is also\nnot a valid way to \"materialize\" the prvalue into a glvalue in C++,\nbecause the region represents the *old* storage (sometimes very old), not\nthe *future* storage.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SVals.h"], "_embedding_id": "api:75a14f374e5263695cdb535a", "_similarity": 0.661008358001709, "_retrieval": "embedding"}, {"id": "api:07f9154ceaf117fd3a90a68a", "kind": "method", "name": "getOriginalRegion", "qualified_name": "clang::ento::BlockDataRegion::getOriginalRegion", "namespace": "clang::ento", "owner_id": "type:b27c9fa49a682a28658d48d7", "owner_name": "clang::ento::BlockDataRegion", "signature": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: explicit referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getOriginalRegion() const { return cast<VarRegion>(*OriginalR); } bool operator==(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R == R; } bool operator!=(const referenced_vars_iterator &I) const { assert((R == nullptr) == (I.R == nullptr)); return I.R != R; } referenced_vars_iterator &operator++() { ++R; ++OriginalR; return *this; } // This isn't really a conventional iterator. // We just implement the deref as a no-op for now to make range-based for // loops work. const referenced_vars_iterator &operator*() const { return *this; } }", "return_type": "class referenced_vars_iterator { const MemRegion * const *R; const MemRegion * const *OriginalR; public: referenced_vars_iterator(const MemRegion * const *r, const MemRegion * const *originalR) : R(r), OriginalR(originalR) {} LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *getCapturedRegion() const { return cast<VarRegion>(*R); } LLVM_ATTRIBUTE_RETURNS_NONNULL const VarRegion *", "parameters": [], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/MemRegion.h"], "_embedding_id": "api:07f9154ceaf117fd3a90a68a", "_similarity": 0.6609539985656738, "_retrieval": "embedding"}, {"id": "api:59a9120121473d39ba2a4401", "kind": "method", "name": "getSValAsScalarOrLoc", "qualified_name": "clang::ento::ProgramState::getSValAsScalarOrLoc", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "SVal getSValAsScalarOrLoc(const MemRegion *R) const", "return_type": "SVal", "parameters": [{"position": 0, "name": "R", "type": "const MemRegion *", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Return the value bound to the specified location, assuming\nthat the value is a scalar integer or an enumeration or a pointer.\nReturns UnknownVal() if none found or the region is not known to hold\na value of such type.", "definition": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_embedding_id": "api:59a9120121473d39ba2a4401", "_similarity": 0.658152163028717, "_retrieval": "embedding"}, {"id": "api:bb5d1fac98d62b06da1c9530", "kind": "method", "name": "addTransition", "qualified_name": "clang::ento::CheckerContext::addTransition", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "ExplodedNode *addTransition(ProgramStateRef State = nullptr, const ProgramPointTag *Tag = nullptr)", "return_type": "ExplodedNode *", "parameters": [{"position": 0, "name": "State", "type": "ProgramStateRef", "canonical_type": null, "default_value": "nullptr"}, {"position": 1, "name": "Tag", "type": "const ProgramPointTag *", "canonical_type": null, "default_value": "nullptr"}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Generates a new transition in the program state graph\n(ExplodedGraph). Uses the default CheckerContext predecessor node.\n\n@param State The state of the generated node. If not specified, the state\n       will not be changed, but the new node will have the checker's tag.\n@param Tag The tag is used to uniquely identify the creation site. If no\n       tag is specified, a default tag, unique to the given checker,\n       will be used. Tags are used to prevent states generated at\n       different sites from caching out.\nNOTE: If the State is unchanged and the Tag is nullptr, this may return a\nnode which is not tagged (instead of using the default tag corresponding\nto the active checker). This is arguably a bug and should be fixed.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 193, "end_line": 196, "code": "ExplodedNode *addTransition(ProgramStateRef State = nullptr,\n                              const ProgramPointTag *Tag = nullptr) {\n    return addTransitionImpl(State ? State : getState(), false, nullptr, Tag);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:8914c5ed6dc0f00387b69627", "kind": "method", "name": "emitReport", "qualified_name": "clang::ento::CheckerContext::emitReport", "namespace": "clang::ento", "owner_id": "type:7f7641c5ddc8eab0f238c2c5", "owner_name": "clang::ento::CheckerContext", "signature": "void emitReport(std::unique_ptr<BugReport> R)", "return_type": "void", "parameters": [{"position": 0, "name": "R", "type": "std::unique_ptr<BugReport>", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Emit the diagnostics report.", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h", "start_line": 288, "end_line": 291, "code": "void emitReport(std::unique_ptr<BugReport> R) {\n    Changed = true;\n    Eng.getBugReporter().emitReport(std::move(R));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "kind": "method", "name": "get", "qualified_name": "clang::ento::ProgramState::get", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> typename ProgramStateTrait<T>::data_type get() const", "return_type": "typename ProgramStateTrait<T>::data_type", "parameters": [], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": "public", "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 427, "end_line": 431, "code": "template <typename T>\n  typename ProgramStateTrait<T>::data_type\n  get() const {\n    return ProgramStateTrait<T>::MakeData(FindGDM(ProgramStateTrait<T>::GDMIndex()));\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:a632ec38e93b776dc3ad7723", "kind": "method", "name": "remove", "qualified_name": "clang::ento::ProgramState::remove", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef remove(typename ProgramStateTrait<T>::key_type K) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "K", "type": "typename ProgramStateTrait<T>::key_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 828, "end_line": 831, "code": "template<typename T>\nProgramStateRef ProgramState::remove(typename ProgramStateTrait<T>::key_type K) const {\n  return getStateManager().remove<T>(this, K, get_context<T>());\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:27be6c71f8737ec8709572f6", "kind": "method", "name": "set", "qualified_name": "clang::ento::ProgramState::set", "namespace": "clang::ento", "owner_id": "type:89e6b7a10b6e24168e7b159e", "owner_name": "clang::ento::ProgramState", "signature": "template <typename T> [[nodiscard]] ProgramStateRef set(typename ProgramStateTrait<T>::data_type D) const", "return_type": "[[nodiscard]] ProgramStateRef", "parameters": [{"position": 0, "name": "D", "type": "typename ProgramStateTrait<T>::data_type", "canonical_type": null, "default_value": null}], "template_parameters": [{"name": "T", "kind": "type", "declared_type": null, "is_pack": false, "default_value": null}], "access": null, "qualifiers": {"const": true, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h", "start_line": 844, "end_line": 847, "code": "template<typename T>\nProgramStateRef ProgramState::set(typename ProgramStateTrait<T>::data_type D) const {\n  return getStateManager().set<T>(this, D);\n}"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/ProgramState.h"], "_retrieval": "metaop_api_ref"}, {"id": "api:432eb5b9ff50440a0794eb99", "kind": "method", "name": "isDead", "qualified_name": "clang::ento::SymbolReaper::isDead", "namespace": "clang::ento", "owner_id": "type:0f638a5e3926be17bca4229e", "owner_name": "clang::ento::SymbolReaper", "signature": "bool isDead(SymbolRef sym)", "return_type": "bool", "parameters": [{"position": 0, "name": "sym", "type": "SymbolRef", "canonical_type": null, "default_value": null}], "template_parameters": [], "access": "public", "qualifiers": {"const": false, "static": false, "virtual": false, "pure_virtual": false, "override": false, "noexcept": false}, "category": "framework_api", "callbacks": [], "comment": "Returns whether or not a symbol has been confirmed dead.\n\nThis should only be called once all marking of dead symbols has completed.\n(For checkers, this means only in the checkDeadSymbols callback.)", "definition": {"source_type": "h", "file": "clang/include/clang/StaticAnalyzer/Core/PathSensitive/SymbolManager.h", "start_line": 629, "end_line": 631, "code": "bool isDead(SymbolRef sym) {\n    return !isLive(sym);\n  }"}, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/PathSensitive/SymbolManager.h"], "_retrieval": "metaop_api_ref"}, {"id": "type:9dd6ea9e6fc40f462913fff1", "kind": "class", "name": "ASTCodeBody", "qualified_name": "clang::ento::check::ASTCodeBody", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 48, "end_line": 61, "code": "class ASTCodeBody {\n  template <typename CHECKER>\n  static void _checkBody(void *checker, const Decl *D, AnalysisManager& mgr,\n                         BugReporter &BR) {\n    ((const CHECKER *)checker)->checkASTCodeBody(D, mgr, BR);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBody(CheckerManager::CheckDeclFunc(checker,\n                                                       _checkBody<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}, {"id": "type:0cd555dadc4121b45bcf8014", "kind": "class", "name": "BranchCondition", "qualified_name": "clang::ento::check::BranchCondition", "namespace": "clang::ento::check", "bases": [], "template_parameters": [], "callbacks": [], "owner_id": null, "owner_name": null, "access": null, "availability": "public_framework", "reusable": true, "required_includes": ["clang/StaticAnalyzer/Core/Checker.h"], "comment": "", "source": {"file": "clang/include/clang/StaticAnalyzer/Core/Checker.h", "start_line": 299, "end_line": 313, "code": "class BranchCondition {\n  template <typename CHECKER>\n  static void _checkBranchCondition(void *checker, const Stmt *Condition,\n                                    CheckerContext & C) {\n    ((const CHECKER *)checker)->checkBranchCondition(Condition, C);\n  }\n\npublic:\n  template <typename CHECKER>\n  static void _register(CHECKER *checker, CheckerManager &mgr) {\n    mgr._registerForBranchCondition(\n      CheckerManager::CheckBranchConditionFunc(checker,\n                                               _checkBranchCondition<CHECKER>));\n  }\n}"}, "_retrieval": "required_framework"}]
Known MetaOps:
[{"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkLocation"], "kind": "detection", "meta_op": "Read RegionState on memory access and report use of a released allocation.", "behavior": {"preconditions": [], "state_reads": ["RegionState[accessed symbol]"], "state_writes": [], "transitions": [], "reports": ["Use of memory after it is freed"]}, "meta_impl": "void MallocChecker::checkLocation(SVal l, bool isLoad, const Stmt *S,\n                                  CheckerContext &C) const {\n  SymbolRef Sym = l.getLocSymbolInBase();\n  if (Sym) {\n    checkUseAfterFree(Sym, C, S);\n    checkUseZeroAllocated(Sym, C, S);\n  }\n\nvoid MallocChecker::HandleUseAfterFree(CheckerContext &C, SourceRange Range,\n                                       SymbolRef Sym) const {\n  const UseFree *Frontend = getRelevantFrontendAs<UseFree>(C, Sym);\n  if (!Frontend)\n    return;\n  if (!Frontend->isEnabled()) {\n    C.addSink();\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkLocation", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3668, "end_line": 3674}, {"role": "report_helper", "symbol": "MallocChecker::HandleUseAfterFree", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2798, "end_line": 2806}], "api_refs": [{"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}, {"id": "api:8914c5ed6dc0f00387b69627", "qualified_name": "clang::ento::CheckerContext::emitReport"}], "depends_on": ["metaop:755cd4eed00d6aa938b1493d"], "_embedding_id": "metaop:0c42cf4c9057aa4b060de371", "_similarity": 0.7672107815742493, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "state_transition", "meta_op": "Validate a deallocation and mark the released symbol in RegionState.", "behavior": {"preconditions": [], "state_reads": ["RegionState[released symbol]"], "state_writes": ["RegionState[released symbol] = released"], "transitions": [], "reports": []}, "meta_impl": "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr,\n                          const CallEvent &Call, ProgramStateRef State,\n                          bool Hold, bool &IsKnownToBeAllocated,\n                          AllocationFamily Family, bool ReturnsNullOnFailure,\n                          std::optional<SVal> ArgValOpt) const {\n\n  if (!State)\n    return nullptr;\n\n  SVal ArgVal = ArgValOpt.value_or(C.getSVal(ArgExpr));\n  if (!isa<DefinedOrUnknownSVal>(ArgVal))\n    return nullptr;\n  DefinedOrUnknownSVal location = ArgVal.castAs<DefinedOrUnknownSVal>();\n\n  // Check for null dereferences.\n  if (!isa<Loc>(location))\n    return nullptr;\n\n  // The explicit NULL case, no operation is performed.\n  ProgramStateRef notNullState, nullState;\n  std::tie(notNullState, nullState) = State->assume(location);\n  if (nullState && !notNullState)\n    return nullptr;\n\n  // Unknown values could easily be okay\n  // Undefined values are handled elsewhere\n  if (ArgVal.isUnknownOrUndef())\n    return nullptr;\n\n  const MemRegion *R = ArgVal.getAsRegion();\n  const Expr *ParentExpr = Call.getOriginExpr();\n\n  // NOTE: We detected a bug, but the checker under whose name we would emit the\n  // error c", "source_spans": [{"role": "helper", "symbol": "MallocChecker::FreeMemAux", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 2315, "end_line": 2974}], "api_refs": [{"id": "api:1523abd1f161565ea1668250", "qualified_name": "clang::ento::ProgramState::set"}, {"id": "api:580faeb0c4c90b1b2c353a9c", "qualified_name": "clang::ento::ProgramState::get"}], "depends_on": ["metaop:97f65925f14ff701701ae673"], "_embedding_id": "metaop:755cd4eed00d6aa938b1493d", "_similarity": 0.7670662999153137, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:adb829186e42f7350171e28e", "name": "NewDelete", "registration_function": "ento::registerNewDeleteChecker", "frontend_member": "NewDeleteChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}, {"id": "frontend:57d20d71e6adfd69d4ec7b73", "name": "MismatchedDeallocator", "registration_function": "ento::registerMismatchedDeallocatorChecker", "frontend_member": "MismatchedDeallocatorChecker"}, {"id": "frontend:fbf7126932cb777361353b6d", "name": "TaintedAlloc", "registration_function": "ento::registerTaintedAllocChecker", "frontend_member": "TaintedAllocChecker"}], "callbacks": ["MallocChecker::checkPreCall"], "kind": "entry_filter", "meta_op": "Dispatch recognized deallocation and allocation calls to checker-local models.", "behavior": {"preconditions": [], "state_reads": [], "state_writes": [], "transitions": [], "reports": []}, "meta_impl": "void MallocChecker::checkPreCall(const CallEvent &Call,\n                                 CheckerContext &C) const {\n\n  if (const auto *DC = dyn_cast<CXXDeallocatorCall>(&Call)) {\n    const CXXDeleteExpr *DE = DC->getOriginExpr();\n\n    // FIXME: I don't see a good reason for restricting the check against\n    // use-after-free violations to the case when NewDeleteChecker is disabled.\n    // (However, if NewDeleteChecker is enabled, perhaps it would be better to\n    // do this check a bit later?)\n    if (!NewDeleteChecker.isEnabled())\n      if (SymbolRef Sym = C.getSVal(DE->getArgument()).getAsSymbol())\n        checkUseAfterFree(Sym, C, DE->getArgument());\n\n    if (!isStandardNewDelete(DC->getDecl()))\n      return;\n\n    ProgramStateRef State = C.getState();\n    bool IsKnownToBeAllocated;\n    State = FreeMemAux(\n        C, DE->getArgument(), Call, State,\n        /*Hold*/ false, IsKnownToBeAllocated,\n        AllocationFamily(DE->isArrayForm() ? AF_CXXNewArray : AF_CXXNew));\n\n    C.addTransition(State);\n    return;\n  }", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkPreCall", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3445, "end_line": 3471}], "api_refs": [], "depends_on": [], "_embedding_id": "metaop:97f65925f14ff701701ae673", "_similarity": 0.75016188621521, "_retrieval": "embedding"}, {"checker_id": "checker:6e8ffa295564d2873b883c5c", "implementation_class": "MallocChecker", "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.", "analysis_mode": "path_sensitive", "frontends": [{"id": "frontend:06f69d363efa4ce08f748e88", "name": "Malloc", "registration_function": "ento::registerMallocChecker", "frontend_member": "MallocChecker"}, {"id": "frontend:6d020c6bb3d198f9e93fbc02", "name": "NewDeleteLeaks", "registration_function": "ento::registerNewDeleteLeaksChecker", "frontend_member": "NewDeleteLeaksChecker"}], "callbacks": ["MallocChecker::checkDeadSymbols"], "kind": "lifecycle_cleanup", "meta_op": "Collect allocated dead symbols as leaks and remove dead allocation state.", "behavior": {"preconditions": [], "state_reads": ["RegionState entries"], "state_writes": ["remove dead allocation state"], "transitions": [], "reports": ["memory leak"]}, "meta_impl": "void MallocChecker::checkDeadSymbols(SymbolReaper &SymReaper,\n                                     CheckerContext &C) const\n{\n  ProgramStateRef state = C.getState();\n  RegionStateTy OldRS = state->get<RegionState>();\n  RegionStateTy::Factory &F = state->get_context<RegionState>();\n\n  RegionStateTy RS = OldRS;\n  SmallVector<SymbolRef, 2> Errors;\n  for (auto [Sym, State] : RS) {\n    if (SymReaper.isDead(Sym)) {\n      if (State.isAllocated() || State.isAllocatedOfSizeZero())\n        Errors.push_back(Sym);\n      // Remove the dead symbol from the map.\n      RS = F.remove(RS, Sym);\n    }\n  }\n\n  if (RS == OldRS) {\n    // We shouldn't have touched other maps yet.\n    assert(state->get<ReallocPairs>() ==\n           C.getState()->get<ReallocPairs>());\n    assert(state->get<FreeReturnValue>() ==\n           C.getState()->get<FreeReturnValue>());\n    return;\n  }\n\n  // Cleanup the Realloc Pairs Map.\n  ReallocPairsTy RP = state->get<ReallocPairs>();\n  for (auto [Sym, ReallocPair] : RP) {\n    if (SymReaper.isDead(Sym) || SymReaper.isDead(ReallocPair.ReallocatedSym)) {\n      state = state->remove<ReallocPairs>(Sym);\n    }\n  }\n\n  // Cleanup the FreeReturnValue Map.\n  FreeReturnValueTy FR = state->g", "source_spans": [{"role": "callback_segment", "symbol": "MallocChecker::checkDeadSymbols", "file": "clang/lib/StaticAnalyzer/Checkers/MallocChecker.cpp", "start_line": 3132, "end_line": 3469}], "api_refs": [{"id": "api:432eb5b9ff50440a0794eb99", "qualified_name": "clang::ento::SymbolReaper::isDead"}, {"id": "api:4db73b63e0c13374bd4f2d68", "qualified_name": "clang::ento::ProgramState::remove"}, {"id": "api:2669ca957a0ccf39ad92c422", "qualified_name": "clang::ento::CheckerContext::addTransition"}], "depends_on": ["metaop:ab94c1766baa204d15b85804"], "_embedding_id": "metaop:72d54c7d67e9a0cbaf78dcc9", "_similarity": 0.74986732006073, "_retrieval": "embedding"}]
