# CSA Checker 工厂模式合并说明

更新时间：2026-08-09

本文面向主工程工厂模式合并，按当前代码和实际产物说明 CSA checker 的整体生成逻辑、输入、输出和接口边界。下一阶段的语义增强策略暂不在本文实现。

## 一、整体流程

CSA 生成流程沿用 CodeQL 的职责拆分，但最终输出是 Clang Static Analyzer 动态插件。

~~~text
Rule_CSA + Case_CSA
        |
        v
负例逻辑提取（LLM）
        |
        v
MetaOp/API embedding 检索
        |
        v
生成单文件 checker.cpp
        |
        v
clang++ 编译
        |
        +-- 编译错误 -> LLM 分析和修复，最多 max_compiler_trys
        |
        v
首个负例运行验证
        |
        v
全部正/负例回归
        |
        v
语义增强入口（下一阶段重点）
~~~

当前生成单位是一个独立的 .cpp 文件和编译得到的 .so 插件，不生成项目级 .h，不修改 LLVM/Clang 官方源码、Checkers.td 或官方注册表。

## 二、工厂模式需要接入的模块

| 模块 | 作用 |
| --- | --- |
| src/main_csa.py | CLI 入口，加载规则、用例、LLVM 环境和 LLM |
| src/entity/concreteProduct_CSA.py | Case_CSA、Checker_CSA、Rule_CSA 数据对象 |
| src/csa_generator.py | CSACheckerGenerator 主流程 |
| src/plateform/csa.py | clang++ 编译插件、clang --analyze 运行插件 |
| src/retriever/csa_embedding.py | MetaOp/API embedding 索引和检索 |
| src/llm_interface/csa_llm_provider.py | OpenAI-compatible LLM 客户端 |
| src/prompt/csa_prompt/build_prompt.py | CSA 专用 prompt builder |

推荐的工厂调用方式：

~~~python
rule = Rule_CSA.from_rule_record(...)
cases = list[Case_CSA]
generator = CSACheckerGenerator(rule, cases, ...)
generator.generate_checker()
~~~

兼容 CodeQL 风格的公开方法：

~~~python
generator.first_checker_generation()
generator.run_all_test_cases(checker)
generator.checker_augmentation(checker)
generator.runAllTestCases(checker)
~~~

Checker_CSA 的主要字段：

~~~text
checker_code       当前完整 C++ 源码
name               implementation class 名称
frontend           CSA frontend 名称
plugin_path        已编译 .so 的路径
version            checker 版本号
generation_kind    initial 或 augmentation_negative/positive
metadata           规则、用例、轮次等元数据
~~~

## 三、输入

### 1. 规则文件

默认位置：

~~~text
experiment/gjb8114/rule_codeql/jgb8114_all_rules.json
~~~

main_csa.py 使用 --rule-name 按 main_title 查找规则记录。规则描述来自 description。规则 id 和诊断文本优先从首个负例的 CHECK-MESSAGES 中解析。

规则测试目录默认映射为：

~~~text
experiment/gjb8114/codeql_test_case/<rule-name 中的短横线替换为下划线>/
~~~

第三条规则的身份：

~~~text
规则名：use-uncheck-pointer-after-malloc
规则 id：gjb8114-r-1-3-8
诊断：禁止动态分配的指针变量未检查即使用
checker 类：GeneratedUseUncheckPointerAfterMallocChecker
frontend：gjb8114.UseUncheckPointerAfterMalloc
~~~

### 2. 测试用例

load_cases 递归加载 .c、.cc、.cpp、.cxx 文件。

有 expected-warning、expected-error、expected-note 或 CHECK-MESSAGES 的用例是负例；没有预期诊断的用例是正例。每个 Case_CSA 保存：

~~~text
case_code
case_path
case_flag
expected_diagnostics
last_result
~~~

### 3. 官方知识库

以下文件是只读输入：

~~~text
csa_official_checker_logic_extract/csa_meat_op.json
csa_official_api_extract/csa_api.json
~~~

csa_meat_op.json 只保存第二阶段官方 MetaOp。csa_api.json 保存官方 API/type 提取结果。生成 checker 源码不得写回这两个文件。

### 4. Embedding

默认模型：

~~~text
BAAI/bge-large-en-v1.5
~~~

默认缓存：

~~~text
src/embedding_db/csa/
~~~

缓存文件：

~~~text
manifest.json
metaop_records.json
api_records.json
metaop_embeddings.npy
api_embeddings.npy
~~~

manifest 保存模型名以及两个官方 JSON 的 SHA-256。当前索引约有 18 个 MetaOp、2618 条 API/type 记录。官方输入变更后缓存会失效重建。

### 5. 编译和 LLM 环境

~~~text
LLVM 源码：/home/llvm/llvm-project
LLVM build：/home/checker/llvm-build
编译器：/home/checker/llvm-build/bin/clang++
分析器：/home/checker/llvm-build/bin/clang
LLM 配置：csa_official_api_extract/llm_config_csa_meta_op.json
~~~

密钥优先从 CSA_LLM_API_KEY 读取，地址优先从 CSA_LLM_BASE_URL 读取，模型可由 CSA_LLM_MODEL 或 --llm-model 覆盖。密钥不会写入源码、prompt 结果或 JSON。

## 四、A 阶段：首个 checker

1. 按文件名排序选择负例候选。当前实现允许当前候选失败后尝试后续负例；每个候选最多 max_round 轮。
2. 使用规则描述和首负例调用逻辑提取 LLM，得到 JSON logic units。
3. 以规则名、规则描述和 logic units 查询 embedding，取得 MetaOp/API Top-K，并补充 MetaOp 引用的 API。
4. 使用首 checker prompt 生成单个 C++ 文件。要求包含独立 implementation class、clang_registerCheckers 和 clang_analyzerAPIVersionString。
5. 在独立 round workspace 内编译。编译失败时，把当前完整源码、编译输出、规则上下文、检索上下文、编译错误分析和可编译模板交给 LLM 修复。
6. 加载生成的 .so，运行 clang --analyze 验证首负例。编译成功、分析器返回码为 0、并出现目标诊断，才算首 checker 成功。

## 五、B 阶段：全量验证

首 checker 成功后，使用同一个 .so 运行全部用例，不修改 checker 源码：

- 负例没有目标诊断：false_negative；
- 正例产生目标诊断：false_positive；
- 编译失败、分析器崩溃或命令失败：execution_failure；
- 每个结果保存预期诊断、实际诊断、返回码、stdout、stderr 和 failure category。

正式生成入口随后调用 checker_augmentation。当前第三条规则首负例未通过，所以本轮尚未进入正式语义增强阶段。

## 六、输出目录

每条规则的根目录：

~~~text
<result-dir>/csa/<rule-name>/
~~~

典型结构：

~~~text
<rule>/
├── checker_generation_result.json
├── first_checker/
│   ├── negative_case_N/selected_case.cpp
│   ├── negative_case_N/round_M/logic.json
│   ├── negative_case_N/round_M/retrieved_metaops.json
│   ├── negative_case_N/round_M/retrieved_api_refs.json
│   ├── negative_case_N/round_M/logic_prompt.md
│   ├── negative_case_N/round_M/generation_prompt.md
│   ├── negative_case_N/round_M/first_generation/generated_checker.cpp
│   ├── negative_case_N/round_M/first_generation/compile.stdout
│   ├── negative_case_N/round_M/first_generation/compile.stderr
│   ├── negative_case_N/round_M/compiler_failed_try_K/
│   ├── negative_case_N/round_M/workspace/<Checker>.cpp
│   ├── negative_case_N/round_M/workspace/<Checker>.so
│   └── negative_case_N/round_M/verify.output.json
├── augmentation/attempt_N/
└── checker_versions/version_N/
~~~

模型返回保存在对应 .answer.md；请求失败记录在 .errors.log。

当前实际输出：

~~~text
第一条：
result-generation-single-cpp/csa/no-assignment-in-condition/

第二条：
result-generation-second-rule/csa/no-else-branch/

第三条中间产物：
result-generation-third-rule/csa/use-uncheck-pointer-after-malloc/
~~~

第三条因为首 checker 没有通过首负例验证，当前没有正式的 checker_generation_result.json、最终 generated_checker.cpp 或 checker_versions 目录。

## 七、结果 JSON 契约

正式结果包含：

~~~json
{
  "stage": "full_lifecycle",
  "rule": "...",
  "rule_id": "gjb8114-r-...",
  "checker": "Generated...Checker",
  "frontend": "gjb8114....",
  "initial_case": "绝对路径",
  "negative_case_amount": 10,
  "positive_case_amount": 10,
  "success_case_list": [],
  "failed_case_list": [],
  "performance": "20/20",
  "compile_success": true,
  "initial_case_success": true,
  "all_cases_success": true,
  "augmentation_started": true,
  "generation_attempts": 1,
  "compile_attempts": 1,
  "augmentation_attempts": 0,
  "skipped_cases": [],
  "termination_reason": "all_cases_passed",
  "checker_versions": [],
  "total_cost": null,
  "cost_note": "not calculated: model pricing is not configured",
  "token_usage": {},
  "llm_model": "gpt-5.4-mini",
  "retrieval": {},
  "initial_generation_source": "llm",
  "llm_failure_amount": 0,
  "llm_failures": []
}
~~~

success_case_list 和 failed_case_list 的单条记录包含：

~~~text
case_path
case_type
expected_diagnostics
actual_diagnostics
returncode
stdout
stderr
success
failure_category
~~~

成本当前为 null，因为没有配置可靠的模型价格表；token 用量仍然记录。

## 八、当前样例状态

第一条和第二条已经使用真实 embedding、LLM、Clang++ 和 CSA analyzer 完成 20/20 全量回归。第二条真实触发一次编译修复后通过。

第三条 use-uncheck-pointer-after-malloc 已验证：

- embedding 检索正常；
- 逻辑提取和 checker 生成正常；
- 多轮编译错误回传修复正常；
- 生成插件可编译；
- 首负例语义验证未通过，主要表现为没有识别 malloc 后指针的首次解引用；
- 因首 checker 未通过，B 阶段和正式语义增强尚未开始。

本轮未修改 csa_api.json、csa_meat_op.json 或 LLVM 源码。

## 九、工厂合并注意事项

1. 类名、frontend、rule id 和诊断必须从 Rule_CSA 动态传递，不能写死为第一条规则。
2. 不要依赖 .h 文件；CSA 交付物是 Checker_CSA.checker_code 和编译后的 .so。
3. 官方 MetaOp/API JSON 和 embedding cache 是知识库输入，生成器不得回写。
4. 判定必须区分 false_negative、false_positive 和 execution_failure。
5. workspace 是临时编译区，可以清理；源码、prompt、编译日志、验证 JSON 应保留作审计证据。
6. 下一阶段语义增强应复用当前 checker、完整失败结果、已通过用例和检索上下文，并保留回归门禁。本次文档不提前实现增强策略。

