# CSA 扩展设计与第一阶段 API 提取说明

## 1. 项目边界

AutoChecker 的 CSA 扩展按三个相互独立的阶段推进：

```text
第一阶段：LLVM 公开头文件 -> csa_api.json
第二阶段：官方 checker 实现 -> 独立 checker 逻辑数据集
第三阶段：API 与 checker 逻辑分别检索 -> 生成 CSA checker
```

本文档只描述第一阶段。第二阶段尚未实现，后续必须使用独立目录、schema、
JSON、retriever 和 embedding 缓存。`csa_api.json` 不允许出现
`logic_summary`、`detection_steps`、`trigger_conditions`、
`state_transitions`、`reporting_workflow` 等逻辑解释字段。

## 2. 输入与公开 API 策略

提取器使用 Tree-sitter 静态解析，不配置或构建 LLVM，也不调用 CSA。输入为：

```text
clang/include/clang/StaticAnalyzer/**/*.h
clang/lib/StaticAnalyzer/Checkers/**/*.h
clang/lib/StaticAnalyzer/Checkers/**/*.cpp
```

最终 JSON 只保留 `clang/include/clang/StaticAnalyzer/**/*.h` 中声明的：

- 命名空间级符号；
- class 或 struct 的 `public` 成员和嵌套类型。

以下内容会被排除：

- `.cpp` 中独有的 callback、helper 和注册函数；
- `clang/lib/...` 内部头文件中的符号；
- 匿名命名空间中的符号；
- `private` 和 `protected` 成员。

`.cpp` 仍参与声明与定义关联。只有已经存在公开头文件声明时，匹配到的
`.cpp` 定义才会作为该公开 API 的源码证据保存，不能单独产生可检索 API。

“可复用”在 schema 1.1 中严格指上述公开 include 树中的命名空间级或
`public` 符号。`protected` API 不作为通用 checker API 推荐。

## 3. Schema 1.1

顶层结构保持不变：

```json
{
  "metadata": {},
  "types": [],
  "apis": []
}
```

### 3.1 metadata

关键字段包括：

```json
{
  "schema_version": "1.1",
  "input_policy": "public_reusable_only",
  "parser": "tree-sitter-cpp",
  "llvm_revision": "ee779de847774cc935ec089ebb6185c790aedcf7",
  "source_roots": [
    "clang/include/clang/StaticAnalyzer",
    "clang/lib/StaticAnalyzer/Checkers"
  ],
  "parsed_files": 219,
  "files_with_syntax_errors": 71,
  "excluded_counts": {
    "anonymous_namespace": 1964,
    "cpp_only": 969,
    "inaccessible_owner": 0,
    "internal_header": 309,
    "private_member": 326,
    "protected_member": 147
  }
}
```

排除数量按提取器去重后的候选记录统计，不等同于源码文本声明次数。

### 3.2 通用公开性字段

每个 `types` 和 `apis` 记录均包含：

```json
{
  "availability": "public_framework",
  "reusable": true,
  "required_includes": [
    "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"
  ]
}
```

`required_includes` 是声明该符号的直接公开头文件，路径去掉
`clang/include/` 前缀；当前不计算传递 include。

### 3.3 types

`types` 支持 `class`、`struct`、`enum` 和 `type_alias`。

enum 保存是否为 scoped enum、显式底层类型和枚举项：

```json
{
  "kind": "enum",
  "name": "ExplorationStrategyKind",
  "scoped": true,
  "underlying_type": null,
  "enumerators": [
    {
      "name": "DFS",
      "qualified_name": "clang::ExplorationStrategyKind::DFS",
      "value": null,
      "comment": "",
      "source": {}
    }
  ]
}
```

匿名 enum 使用文件路径和起始行生成稳定 ID。只有 enum 本身处于公开上下文时，
其枚举项才会保留。

类型别名同时支持 `using` 和 `typedef`，保存 `alias_syntax`、
`target_type`、owner、访问级别、include 和源码位置。

### 3.4 模板参数

类模板和函数模板均保存：

```json
{
  "template_parameters": [
    {
      "name": "T",
      "kind": "type",
      "declared_type": null,
      "is_pack": false,
      "default_value": "CallEvent"
    }
  ]
}
```

支持类型参数、非类型参数、参数包和默认值。模板声明的 `source.code` 保留完整
`template <...>` 前缀；函数的 `signature` 同样保留此前缀。

### 3.5 apis

`apis` 保存函数、方法、构造函数和析构函数，包括参数、返回类型、默认参数、
访问权限、qualifier、注释、声明及可选定义。`definition.code` 只是 LLVM 原始
源码证据，不是 checker 逻辑拆分结果。

## 4. `.def` 文件限制

第一阶段明确不读取或展开 `.def` 文件。由 `.def` 宏生成的枚举项可能缺失，
也不会通过预处理器补全。JSON 中的枚举项仅代表 Tree-sitter 在目标 `.h/.cpp`
输入内直接识别到的源码声明。

## 5. 当前提取结果

基于 LLVM revision `ee779de84` 的 schema 1.1 全量结果：

| 指标 | 数量 |
|---|---:|
| 已处理文件 | 219 |
| class | 292 |
| struct | 29 |
| enum | 27 |
| type_alias | 132 |
| 类型总数 | 480 |
| constructor | 135 |
| destructor | 33 |
| function | 77 |
| method | 1,893 |
| API 总数 | 2,138 |
| 头文件内定义 | 1,252 |
| 已关联 `.cpp` 定义 | 22 |
| 只有声明 | 864 |
| 带模板参数的类型 | 29 |
| 带模板参数的 API | 79 |

固定回归样例覆盖：

- `CheckerContext::emitReport` 的 include 和可复用性；
- `DivZeroChecker::checkPreStmt`、注册函数及 `.cpp` helper 的排除；
- `ExplorationStrategyKind` 和 `PointerEscapeKind`；
- `SymbolRef` 的 `using` 与 `ProgramStateRef` 的 `typedef`；
- `CallEventRef<T = CallEvent>` 的默认参数；
- `Checker<typename... CHECKs>` 的参数包；
- 所有输出记录的公开性与 include 字段。

## 6. 暂不实现项

以下内容不属于本次 schema 1.1 补全：

- ProgramState 注册宏；
- canonical type；
- 每条记录的 `parse_quality`；
- 正式 JSON Schema 文件；
- checker 逻辑拆分及任何逻辑字段。

第二阶段开始时应新建例如
`csa_official_checker_logic_extract/collect_checker_logic.py`，并输出独立的
`csa_checker_logic.json`。不得修改第一阶段数据边界。
