# 子代理模型与思考强度契约

所有 personal-dev 入口共用本契约，只维护 `worker`、`reviewer` 两类子代理配置；主会话模型与强度不变，也不用于选型。

## 显式参数与入口校验

`dev-delegate` / `dev-auto` 必填本次显式 worker + reviewer；`dev-review` 只需 reviewer，可选 worker 提供时同样校验，不因此派发执行代理。后续确需执行型子代理才要求 worker，不增加权限。规范格式为 `worker=<model>:<effort> reviewer=<model>:<effort>`，等价写法包括：

```text
$dev-delegate w 6luna high r 6.1terra high
$dev-delegate w 6luna:high r 6.1terra:high
$dev-delegate w=6luna:high r=6.1terra:high
$dev-auto worker gpt-6-luna high reviewer gpt-6.1-terra high
$dev-review reviewer=6.1terra:HIGH
```

入口名按当前客户端使用，型号仅作示例。worker 别名为 `worker / work / w / code`，reviewer 为 `reviewer / review / r / check`，不区分大小写；角色与值用 `=`、`:` 或空白分隔，值用 `<model>:<effort>` 或 `<model> <effort>`，符号两侧可有空白，各参数可混用。输出、ledger、派发只使用两个规范角色名。

每项恰好一次且 model / effort 非空；同一角色的别名重复，即使值相同也 BLOCKED，不覆盖。缺项、额外值、非法或歧义参数、旧 `plan / final` 角色与旧强度覆写参数均 BLOCKED，列出安全原因、缺项及入口规范格式。

参数仅从本次调用提取，与任务正文分开；不从示例、PLAN、历史会话、ledger、缓存或默认配置补值。dev-delegate / dev-review 在读取需求或源码、创建报告和派发前校验；dev-auto 在读取准备契约及生成 SPEC / PLAN 前校验，将同一对已验证配置传给执行器。dev-prepare / dev-simplify / dev-runtime-check 无子代理时无需参数，获准转入委派时才在交接入口校验。

## 当前 Harness 校验

顺序固定为：解析角色 / model / effort → 常见格式归一化 → 与本轮实际子代理模型清单唯一匹配 → 校验该型号的 effort → 展示精确配置并执行。语义明确的格式差异不阻塞：

- 模型忽略大小写；完整数字版本 + 系列名可省略 `gpt` 前缀及前缀后、版本与系列间的连字符。`6luna / 6-luna / gpt6luna / gpt-6-luna` 同键，`6.1terra / 6.1-terra / gpt6.1terra / gpt-6.1-terra` 同理。保留小数点与完整系列名；其他原生 ID 仅忽略大小写，不模糊匹配或为 `terra` 补版本。
- 请求和清单用相同归一化规则，必须恰好命中一个实际 ID；零命中或重名均 BLOCKED，不以 effort、精确拼写优先级、代际、价格、能力或最新版本挑型号。
- effort 忽略大小写，仅额外支持 `h → high`、`m → medium`；必须唯一匹配所选型号支持的值，不推断缺项、不把非法值替换为其他等级、不换模型满足强度。

校验所有必需及额外提供的角色，依据必须是本轮工具的型号、各型号 effort 和覆写能力；reviewer 单参数无需 worker 型号或执行能力。缺少名单、支持证据、独立上下文或实际覆写能力，型号不可用或 effort 不支持，均立即 BLOCKED，说明 Harness、角色与缺口。不替换模型、不升降 effort、不 fallback、不继承默认或由主模型代做；不改全局设置、嵌套客户端补能力。原生拒绝或返回不同配置时停止，报告请求值与原因，不重试另一配置。

Codex 的共享 helper 协议见 [Codex adapter](codex.md#模型校验与显示)；其他 Harness 按各自 adapter 与本轮原生 schema 等价校验，不运行该 Python helper。成功后只展示已提供角色的 `<角色> 模型：<实际 ID>｜思考强度：<effort>`，使用当前清单的精确值直接执行，不再确认。

## 所有子代理的传递规则

| 子代理工作 | 唯一模型配置 |
| --- | --- |
| 写代码、搜索/读取文件、查引用、执行命令、修改配置、补测试、初次 Coder、修复与按需 fresh coder | `worker` |
| 代码审查、SPEC / PLAN 符合性、验证结果与回归风险检查、独立检查、任务验收、复验、Final Reviewer | `reviewer` |

同角色的并行、新建、重建、修复及 Final Reviewer 均用同一配置，不新增规划 / 终审专用角色。Reviewer 检查验证证据，有副作用的验证由主模型安排 Worker；困难审查先补证据和裁决，不自动升级强度。独立验收、只读、禁止子代理再派生、并行范围及槽位限制仍适用。

恢复时重新校验本次显式配置并与已有代理核对；不一致或无法核验则停止续接并说明。保留累计修复次数、证据和运行中代理状态，fresh coder 条件、三轮预算、失败隔离及终审条件依入口契约，不因配置归一化改变。
