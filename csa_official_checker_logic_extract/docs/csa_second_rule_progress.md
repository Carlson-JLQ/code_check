# CSA 第二条 GJB8114 规则生成进度

更新时间：2026-08-09

## 当前结论

第二条规则 `no-else-branch` 已完成真实 embedding 检索、LLM 生成、编译修复、
首负例验证和 20 个共享用例全量回归。

- 规则编号：`gjb8114-r-1-4-1`
- 规则含义：包含 `else if` 的条件链必须具有最终 `else` 分支
- implementation class：`GeneratedNoElseBranchChecker`
- frontend：`gjb8114.NoElseBranch`
- 生成模型：`gpt-5.4-mini`
- embedding 模型：`BAAI/bge-large-en-v1.5`
- 测试结果：负例 10/10，正例 10/10，总计 20/20
- 生成文件：单个 `.cpp`，不生成项目头文件

## 本轮改造

生成器已移除第一条规则的身份硬编码。checker 类名和 frontend 由规则名动态生成，
规则编号和诊断文本从负例的 `CHECK-MESSAGES` 自动提取，测试目录由 `--rule-name`
自动映射。

通用生成模板只提供 Clang 24 插件 ABI、注册函数和正确的 AST 诊断写法，不提供某条
规则的检测逻辑。具体逻辑来自当前规则描述、首负例、LLM 逻辑提取以及 embedding
检索到的 MetaOp/API。

编译失败时默认最多执行两次 LLM 修复。修复输入包括：

- 当前完整 checker `.cpp`；
- 编译 stdout/stderr；
- 原始规则、规则编号、诊断文本和首负例；
- LLM 提取的逻辑；
- embedding 检索到的 MetaOp/API；
- LLM 编译错误分析；
- 当前 Clang 24 可编译插件模板。

增强阶段也已改为传递完整检查结果，包括 expected/actual diagnostics、return code、
stdout/stderr 和 failure category，并继续复用同一套两次编译修复循环。由于本轮首版
checker 全量通过，增强逻辑未实际触发。

## 实际修复记录

初版 checker 的检测思路正确，但首次编译误用了不存在的 `IfStmt::getParentIf()`，并有
3 处 `AnalysisDeclContext` const 类型不匹配。生成器保存编译日志后调用 LLM 进行第 1 次
修复，修复版本随即编译成功；未使用第 2 次修复机会。

最终统计：

```text
generation_attempts: 1
compile_attempts: 2
augmentation_attempts: 0
performance: 20/20
termination_reason: all_cases_passed
initial_generation_source: llm
llm_failure_amount: 0
```

## 产物位置

- 结构化结果：`result-generation-second-rule/csa/no-else-branch/checker_generation_result.json`
- 最终首版源码：`result-generation-second-rule/csa/no-else-branch/first_checker/generated_checker.cpp`
- 首次编译日志：`first_checker/negative_case_1/round_1/first_generation/`
- 第一次修复后编译日志：`first_checker/negative_case_1/round_1/compiler_failed_try_1/`
- 生成、检索和修复 prompt：`first_checker/negative_case_1/round_1/`
- 动态插件：round workspace 中的 `GeneratedNoElseBranchChecker.so`

## 下一步

1. 选择一条会产生语义失败的复杂规则，真实演练增强阶段，而不仅是单元测试覆盖。
2. 优化长 MetaOp/API 上下文的 token 用量，同时保留编译修复所需信息。
3. 继续验证路径敏感规则，例如动态分配指针使用前检查。
