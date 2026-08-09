# CSA Checker 当前进度

更新时间：2026-08-09

## 一、当前结论

CSA 首个 Checker 的 A/B 阶段已经完成代码实现，并通过真实 Clang Static
Analyzer 环境验证，不再仅是 Mock 流程。

当前目标规则为官方 `DivZeroChecker` 的确定性除零语义，生成 Checker 为：

```text
实现类：GeneratedDivZeroChecker
Frontend：autochecker.GeneratedDivZero
诊断信息：Division by zero
```

真实验证结果：

```text
Checker 插件编译：成功
Checker 动态加载：成功
负例诊断验证：成功
正例无告警验证：成功
A 阶段首例验证：成功
B 阶段准备测试：2/2 通过
源码增强：未启动
```

## 二、编译环境

- LLVM 源码目录：`/home/llvm/llvm-project`
- LLVM revision：`ee779de847774cc935ec089ebb6185c790aedcf7`
- LLVM 独立构建目录：`/home/checker/llvm-build`
- Clang：`24.0.0git`
- Clang 可执行文件：`/home/checker/llvm-build/bin/clang`
- 构建类型：Release
- LLVM target：X86
- 构建工具：CMake 3.22.1、Ninja 1.10.1
- 宿主编译器：GCC/G++ 11.4.0
- 服务器配置：8 核 CPU、约 15 GiB 内存
- CSA Static Analyzer：已启用
- Clang plugin：已启用

LLVM 官方源码树未被修改。生成 Checker 使用动态插件 `.so` 加载，不需要修改
官方 `Checkers.td` 或 Checker `CMakeLists.txt`。

构建复现命令：

```bash
ninja -C /home/checker/llvm-build -j6 clang SampleAnalyzerPlugin
```

## 三、已实现代码

### 1. CSA 实体

文件：`src/entity/concreteProduct_CSA.py`

已实现：

- `Case_CSA`
- `Checker_CSA`
- `Rule_CSA`

### 2. CSA 平台适配

文件：`src/plateform/csa.py`

已实现：

- 将生成的 C++ Checker 编译为动态插件；
- 加载 LLVM 源码头文件和 build 生成头文件；
- 通过 Clang `-load` 加载 Checker；
- 指定 `autochecker.GeneratedDivZero` 运行 analyzer；
- 捕获返回码、stdout 和 stderr；
- 将工具缺失和进程异常记录为执行失败。

### 3. CSA A/B 生成器

文件：`src/csa_generator.py`

已实现：

- 解析 `expected-warning`；
- 只选择第一个未跳过负例；
- 从 `csa_meat_op.json` 检索 DivZero MetaOp；
- 从 `csa_api.json` 解析对应 API 引用；
- 生成 Checker `.cpp` 和 `.h`；
- 生成标准 CSA 插件注册函数；
- 使用 `max_compiler_trys` 限制编译次数；
- 支持注入 LLM 进行编译错误修复；
- 完成首个负例验证；
- 使用同一份初版 Checker 运行全部准备测试；
- 区分 false positive、false negative 和 execution failure；
- 输出 A 阶段中间产物和 B 阶段结果 JSON。

### 4. 命令行入口

文件：`src/main_csa.py`

运行方式：

```bash
cd /home/checker/code_check
PYTHONPATH=src python src/main_csa.py csa_test_cases/div_zero \
  --result-dir result-generation
```

## 四、真实测试结果

已准备测试：

- 负例：`csa_test_cases/div_zero/negative.cpp`
- 正例：`csa_test_cases/div_zero/positive.cpp`

负例实际诊断：

```text
warning: Division by zero [autochecker.GeneratedDivZero]
```

正例实际诊断为空，analyzer 返回码为 0。

最终结果：

```json
{
  "stage": "A+B",
  "checker": "GeneratedDivZeroChecker",
  "negative_case_amount": 1,
  "positive_case_amount": 1,
  "compile_success": true,
  "initial_case_success": true,
  "all_cases_success": true,
  "augmentation_started": false
}
```

完整结果位于：

```text
result-generation/csa/div-zero/checker_generation_result.json
```

生成插件位于：

```text
result-generation/csa/div-zero/first_checker/workspace/
GeneratedDivZeroChecker.so
```

## 五、测试与数据边界

已完成 3 项聚焦单元测试：

1. 只选择第一个未跳过负例；
2. 正确解析 `expected-warning`；
3. A/B 流程正确写入结果 JSON。

两个知识数据集按只读方式使用，验证后 SHA-256 为：

```text
csa_api.json
7e098ca5bfc2d4a89a1b757581d3e5d7d458a2a3c07f4de25ad8ed233d0f4b67

csa_meat_op.json
3ae6e2f3c9af4a8589ac9788f6b350feda3e19e0cdc27ff1a594d7ad1ae9ed48
```

## 六、当前尚未完成

- 当前真实测试集只有一个负例和一个正例；
- 尚未覆盖分支、取余、复合赋值和更多符号值场景；
- 当前成功源码使用离线确定性 DivZero fallback；
- 尚未完成真实 LLM 生成结果的集成验证；
- 尚未真实触发一次 LLM 编译修复循环；
- 尚未实现 Checker augmentation；
- 尚未实现 TaintedDiv frontend；
- 尚未实现 `SimpleStreamChecker` 和 `MallocChecker`；
- 尚未实现多版本选择、自动回滚和多个 frontend 统一生成。

## 七、下一步计划

1. 扩充 DivZero 正负例，覆盖除法、取余、复合赋值、条件分支和符号值；
2. 使用当前不变的初版 Checker 建立完整 B 阶段基线；
3. 接入真实 LLM 生成，验证 prompt、源码解析和产物保存；
4. 人为构造一次编译失败，验证有限编译修复循环；
5. 完善多诊断、行偏移、崩溃和超时的结果解析；
6. 在 A/B 基线稳定后开始 augmentation 阶段；
7. DivZero 完成后复用插件流程实现 `SimpleStreamChecker`，再评估
   `MallocChecker`。

## 八、当前里程碑表述

当前可以表述为：

> 已完成 CSA 首个 Checker A/B 基础设施，完成 Clang 24 编译环境搭建，
> 成功生成、编译、动态注册并运行 DivZero Checker 插件，准备的正负例真实
> 验证全部通过。

当前不能表述为：

> 已完成通用 CSA Checker 自动生成，或已覆盖 DivZero 的全部行为。
