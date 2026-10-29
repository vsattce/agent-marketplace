---
name: dev-auto
description: 自动准备与委派开发：仅在用户明确调用时，复用准备流程生成 SPEC / PLAN，自动检查后直接执行 SDD，普通需求无需确认；适用于 Codex、Claude Code、agy 和 dsh 桌面版。
disable-model-invocation: true
---

# 自动准备与委派开发

Only use when explicitly invoked by the user. Codex 使用 `$personal-dev:dev-auto`，Claude Code 使用 `/personal-dev:dev-auto`，agy / dsh 桌面版使用 `/dev-auto`；`$dev-auto` 是本文的入口简称。显式调用本入口即授权本次准备与委派组合流程，普通开发请求不自动触发。

1. 入口首先读取[子代理模型契约](../../references/subagent-models.md)及当前 Harness adapter，本次显式参数的规范格式为 `worker=<model>:<effort> reviewer=<model>:<effort>`，同时接受契约中的空白分隔、模型别名和 effort 简写。复用 dev-delegate 的共享解析与校验，归一化后唯一匹配当前实际模型并校验 effort；缺任一参数立即中断，提示缺项和规范格式，模型或 effort 不支持同样中断。校验必须早于准备流程和文件生成。
2. 读取[准备与消费契约](../../references/preparation.md)，以 **auto 模式**执行 dev-prepare 等价流程：读取用户需求、项目规则和相关代码，生成文件形式的 SPEC / PLAN，自动检查需求、依赖、范围、验收及风险。
3. 无重大问题时记为 AUTO_READY，**不确认 SPEC、PLAN、模型或 effort，直接继续**。仅重大歧义、未授权的破坏性操作、安全边界不清允许集中询问一次；整次流程共用这一次预算，等待明确答复后继续，规则见共用契约。
4. 读取同包 [dev-delegate 执行正文](../dev-delegate/SKILL.md)，将生成的两个文件路径、task-id 与同一对已验证 worker / reviewer 配置传入，在当前主控制上下文执行其默认短路径，按实际风险升级，直到最终核验与已有授权范围内的收尾结束。读取角色与 Harness adapter 规则，修复收敛、并行和 ledger 参考仅按需读取；**不在 Task 之间询问，不再做人工准备确认**。

本次 dev-auto 已授权上述组合执行，无需嵌套调用 Skill 工具或再发 dev-delegate 命令；其他入口仍保持手动触发。模型策略、修复轮次、调度与 Final Review 统一遵循 dev-delegate 及其 references / scripts，本文件不另行定义。

`SPEC > PLAN > Coder interpretation`。Coder / Reviewer 从文件读取既定需求；能力缺失或任务失败按既有执行契约报告，不能把受阻伪报完成。Git、发布、依赖和全局环境权限服从目标项目规则与本次已有授权。
