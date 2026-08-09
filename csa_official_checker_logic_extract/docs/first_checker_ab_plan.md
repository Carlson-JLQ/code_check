# CSA First Checker: A/B Plan

This stage implements only the first two steps of the CSA workflow.

* **A** selects the first non-skipped negative test, retrieves relevant CSA
  logic units and referenced APIs, generates one standalone checker `.cpp`,
  and compiles and verifies it. Compiler repair is bounded by
  `max_compiler_trys`.
* **B** runs that unchanged checker against every prepared CSA test and records
  semantic and execution failures separately.

Generated files live below `result-generation/csa/<rule>/first_checker/` and a
separate checker workspace. The official API and MetaOp JSON files are inputs
only. A generated header is not required: the implementation class and plugin
registration entry points live in the same `.cpp`. Checker augmentation,
taint frontends, and additional checkers are out of scope for this stage.
