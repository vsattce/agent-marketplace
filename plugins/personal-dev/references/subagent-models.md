# 子代理模型与思考强度契约

所有 personal-dev 自定义 Skills 只维护 `worker`、`reviewer` 两类子代理模型配置；主会话保持用户原本选择的模型与强度，不读取或修改主模型配置来决定子代理。

## 显式参数与入口校验

`dev-delegate` / `dev-auto` 调用格式：`worker=<model>:<effort> reviewer=<model>:<effort>`；`dev-review` 默认只需 `reviewer=<model>:<effort>`。例如：

```text
$dev-delegate worker=6-luna:high reviewer=6.1-terra:high
$dev-auto worker=6-luna:high reviewer=6.1-terra:high
$dev-review reviewer=6.1-terra:high
```

使用当前客户端的完整入口名；型号只是示例，必须在当前 Harness 的子代理工具中可用。入口实际必需的参数必须由用户在本次调用中显式提供，每项恰好一次，model 与 effort 均非空。dev-review 不为接口统一强制 worker；兼容旧调用的可选 worker，提供时同样校验，不因此派发执行代理。后续具体流程确需执行型子代理时才显式要求 worker，且不增加现有写入或派发权限。缺必需项立即中断当前 Skill，列出缺项和该入口的正确格式；不得先执行后补参数。重复、非法、旧 `plan / final` 角色或旧强度覆写参数同样 BLOCKED，不混用两套配置。

固定参数别名：worker 接受 `worker / work / w / code`；reviewer 接受 `reviewer / review / r / check`。文本角色名不区分大小写，角色与值之间接受 `=`、`:` 或空白，符号两侧允许空白；完整名称与别名规则相同，各参数可混用分隔方式。例如：

| 角色 | 等号分隔 | 冒号分隔 | 空白分隔 |
| --- | --- | --- | --- |
| reviewer | `r=6luna:high` | `r:6luna:high` | `r 6luna:high` |
| worker | `w=6luna:high` | `w:6luna:high` | `w 6luna:high` |

先归一化角色与分隔符，再检查入口必需角色是否齐全；例如 `$dev-delegate W : 6-luna:high reviewer 6.1-terra:high`、`$dev-review check=6.1-terra:high` 等价于各自完整格式。内部输出、ledger 和 Harness 派发只使用 worker / reviewer，不产生其他角色。同一角色的多个别名同时出现（包括大小写或分隔方式不同、值相同）立即报重复参数，不按最后一个覆盖。

只放宽角色与值之间的分隔方式，值内部仍须完整使用 `<model>:<effort>`，不接受内部空白、缺项或额外冒号；model 与 effort 保留原始大小写，不补连字符、不纠正型号或推断强度。表中的 `6luna` 只展示参数语法，是否可用仍由当前 Harness 模型清单决定，不新增模型别名。无法明确解析时 BLOCKED。

`dev-delegate`、`dev-review` 在入口首先校验，早于需求文件读取、报告创建与正式派发。`dev-auto` 会间接委派，必须在读取准备契约、生成 SPEC / PLAN 前完成参数和 Harness 能力校验；将同一对已验证配置传给执行器，不重新选型。`dev-prepare`、`dev-simplify`、`dev-runtime-check` 当前由主模型处理，无子代理时无需参数；如果获准转入会委派的流程，在交接入口先校验本次显式参数。此契约不增加它们派生代理的权限。

模型参数从本次调用中提取，与任务描述分开；不能从示例、PLAN、旧 ledger、缓存、默认配置或历史会话补值。恢复时重新校验本次显式配置；已有代理配置与之不一致则停止续接，说明差异，不偷偷沿用旧配置。保留修复计数、证据和运行中代理状态。

## 当前 Harness 校验

以本轮实际子代理工具的模型名单、每个型号支持的 effort 以及可用覆写参数为依据，核验入口必需及额外显式提供的配置。dev-review 只传 reviewer 时无需 worker 型号或执行能力。只允许完整 ID，或省略字面 `gpt-` 前缀的精确缩写（如 `6-luna` 对应 `gpt-6-luna`）；缩写必须唯一命中当前名单。其他别名仅在当前工具明确列为可用 ID 时原样使用。不按名称、主模型、代际、价格或能力排序猜映射。

缺少模型名单、effort 支持证据、独立上下文或实际覆写能力时，立即 BLOCKED，说明具体 Harness、角色与缺失能力。模型不可用或 effort 不支持时同样中断；不替换模型、不升降 effort、不继承原生默认、不交由主模型代做。原生调用拒绝或返回不同的实际配置时停止该流程，报告请求值与失败原因；不重试另一配置、不修改全局设置或嵌套客户端补能力。

Codex 使用 [Codex adapter](codex.md) 及共享 helper；其他 Harness 按对应 adapter 和本轮 schema 做等价校验，无需 Python。校验成功后只展示已提供角色的 `worker 模型：<实际 ID>｜思考强度：<effort>` / `reviewer 模型：<实际 ID>｜思考强度：<effort>`，直接执行，已有明确参数不再询问确认。

## 所有子代理的传递规则

| 子代理工作 | 唯一模型配置 |
| --- | --- |
| 写代码、搜索/读取文件、查引用、执行命令、修改配置、补测试、初次 Coder、修复与按需 fresh coder | `worker` |
| 代码审查、SPEC / PLAN 符合性、验证结果与回归风险检查、独立检查、任务验收、复验、Final Reviewer | `reviewer` |

多个并行 Worker 共享同一 worker 配置，多个 Reviewer 共享同一 reviewer 配置。按任务职责选这两个键，不能为规划、审查、终审或某一轮修复另建模型角色。Reviewer 检查验证证据；需要执行有副作用的验证时仍交主模型安排 Worker。配置一致不代表复用上下文：现有独立验收、只读权限、禁止子代理再派生、并行范围与槽位限制全部保留。

新建、重建和恢复代理均须落实对应配置。Final Reviewer 使用 reviewer，困难审查先补证据并按既有规则裁决，不自动升级思考强度。fresh coder 只在原代理不可恢复、上下文失效或同根因反复无进展时启用，使用同一 worker，不按第三轮机械换人；三轮上限、失败隔离能力和终审触发条件不变。

## Python helper 协议

共享实现为 `skills/dev-delegate/scripts/select_models.py`，dev-review 的同名脚本调用它并指定 `required_roles=("reviewer",)`，无独立选型规则。dev-delegate 的 JSON stdin 必填：

```json
{
  "worker": "6-luna:high",
  "reviewer": "6.1-terra:high",
  "inventory_source": "current-spawn-tool",
  "models": [
    {"id": "gpt-6-luna", "efforts": ["high"]},
    {"id": "gpt-6.1-terra", "efforts": ["high"]}
  ]
}
```

dev-review 的 JSON 必填 reviewer、inventory_source、models，无需 worker；可只提供 reviewer 型号的当前名单。

从显式调用提取的模型参数串可用共享 `parse_arguments` 解析；默认两角色必填，dev-review 传 `required_roles=("reviewer",)`。它只接收模型参数，不接收入口名或任务正文，缺项、重复或非法格式抛出带该入口正确格式的 ValueError，调用方必须停止。JSON 协议保持不变，键使用上述小写固定别名，归一化后只输出已提供的 worker / reviewer；值直接传相同的 `<model>:<effort>` 字符串，不接受其他角色、默认值或主模型元数据。

成功退出 0，输出 `status=READY`、已提供角色的 `{model,effort}` 与对应 `display`；reviewer 单参数只输出 reviewer 和一行 display。失败退出 2，输出 `status=BLOCKED`、安全原因和该入口的 `usage`。不回显不可信输入或异常内容。helper 仅校验传入元数据；主模型负责其本轮真实性和实际原生派发参数，不能把 helper READY 当作已启动或已验证真实模型执行。
