# CSA GJB8114 Checker 完整闭环进度

更新时间：2026-08-09

## 当前结论

首个 GJB8114 CSA checker 已完成真实生成、动态编译、单负例验证和全量回归。

- 规则：`no-assignment-in-condition`
- 规则编号：`gjb8114-r-1-6-3`
- 规则含义：禁止在 `if`、`while`、`do-while`、`for` 等条件表达式中直接执行赋值
- implementation class：`GeneratedNoAssignmentInConditionChecker`
- frontend：`gjb8114.NoAssignmentInCondition`
- 编译器：`/home/checker/llvm-build/bin/clang++`，Clang 24
- analyzer：`/home/checker/llvm-build/bin/clang`
- 测试来源：CodeQL 已有 `no_assignment_in_condition` 测试目录
- 测试结果：负例 10/10，正例 10/10，总计 20/20
- 生成方式：复用 MetaOp 服务配置，`gpt-5.4-mini` 真实生成
- 源码结构：仅生成一个独立 `.cpp`，不生成项目头文件

## 已实现能力

CSA 生成器现在与 CodeQL 生成器采用相同的生命周期：

1. `first_checker_generation()` 从第一个未跳过负例提取逻辑、检索 CSA MetaOp/API、生成源码、编译并验证；失败时支持有限轮次重新生成和有限编译修复。
2. `run_all_test_cases()` / `runAllTestCases()` 对全部共享用例分类执行，分别记录 false negative、false positive、编译/加载/analyzer 执行失败。
3. `checker_augmentation()` 为正例和负例构造不同增强 prompt，候选版本须先通过目标用例，再执行全量回归。
4. 候选 checker 只有在不丢失任何已通过用例且总通过数不下降时才会成为新版本。
5. `generate_checker()` 串联首版生成、全量验证、增强和终止判定。

实现使用独立动态 `.so` 插件，不修改 LLVM/Clang 官方源码树。`csa_api.json` 和
`csa_meat_op.json` 仅作为只读检索输入。默认检索使用本地 `BAAI/bge-large-en-v1.5`，
同时覆盖 API 函数记录和 CSA 回调类型记录；只有显式指定 `--retrieval lexical` 才使用
确定性词法回退。没有 LLM API key 时，首个规则仍能使用确定性源码基线完成编译验证。
CLI 使用 `--use-llm` 时复用 MetaOp 提取配置中的服务地址和密钥，并记录服务端返回的
prompt/completion token。模型价格未配置时不猜测金额。

Embedding 索引已经实际构建：

- MetaOp：18 条
- CSA API/类型：2618 条
- 向量维度：1024
- 模型：`BAAI/bge-large-en-v1.5`
- 缓存：`src/embedding_db/csa/`
- 缓存失效依据：模型标识、`csa_api.json` SHA-256、`csa_meat_op.json` SHA-256

首版生成、编译修复和正/负例增强均调用同一个 embedding retriever。生成 prompt 中保存
带 `_similarity` 和 `_retrieval` 标记的 Top-K 记录；MetaOp 中精确引用的 API 及必要 CSA
回调会在向量 Top-K 后补全，并标记为 `metaop_api_ref` 或 `required_framework`。

## 技术验证

最初使用 `check::BranchCondition` 时得到 19/20：短路表达式
`a == 0 || (b = c)` 的右操作数不在实际分析路径中执行，导致语法违规漏报。当前实现改用
`check::ASTCodeBody` 遍历完整条件 AST，因此短路分支也能被检查，最终达到 20/20。

已通过：

```text
PYTHONPATH=src .venv/bin/python -m unittest \
  src.unit_test.test_csa_llm_provider \
  src.unit_test.test_csa_embedding \
  src.unit_test.test_csa_generator \
  csa_official_checker_logic_extract.tests.test_checker_metaop -v
26 tests passed

PYTHONPATH=src python src/main_csa.py --check-environment
success: true

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=src \
  .venv/bin/python src/main_csa.py --use-llm \
  --llm-model gpt-5.4-mini --result-dir result-generation-single-cpp
performance: 20/20
termination_reason: all_cases_passed
retrieval.mode: embedding
retrieval.dimensions: 1024
initial_generation_source: llm
compile_attempts: 1
augmentation_attempts: 0
```

本次 LLM 调用共使用 20431 tokens；LLM 失败 0 次。新工作区中生成头文件数量为 0，
编译输入只有 `GeneratedNoAssignmentInConditionChecker.cpp`，输出为同名 `.so`。

旧 MetaOp 测试需要项目 `.venv` 中的 `tree_sitter`，系统 Python 无该依赖。因此运行旧测试时应使用：

```text
PYTHONPATH=src .venv/bin/python -m unittest \
  csa_official_checker_logic_extract.tests.test_checker_metaop -v
```

官方知识文件当前 SHA-256：

```text
csa_api.json: 7e098ca5bfc2d4a89a1b757581d3e5d7d458a2a3c07f4de25ad8ed233d0f4b67
csa_meat_op.json: 3ae6e2f3c9af4a8589ac9788f6b350feda3e19e0cdc27ff1a594d7ad1ae9ed48
```

## 产物位置

- 最终结构化结果：`result-generation-single-cpp/csa/no-assignment-in-condition/checker_generation_result.json`
- 首版源码：`result-generation-single-cpp/csa/no-assignment-in-condition/first_checker/generated_checker.cpp`
- 动态插件：首版 round workspace 内的 `GeneratedNoAssignmentInConditionChecker.so`
- 检索记录、生成 prompt、编译日志和单例验证：`first_checker/negative_case_1/round_1/`
- 本地模型：`src/retriever/embedding_model/huggingface/`
- 向量索引：`src/embedding_db/csa/`

## 下一步

1. 选择第二个 GJB8114 规则验证生成器的规则通用性，避免只对首规则有效。
2. 为多处赋值、宏展开、模板代码和条件中的 lambda 增加边界测试。
3. 根据后续规则需要扩充官方 CSA MetaOp 覆盖面，但保持知识库与生成产物分离。
