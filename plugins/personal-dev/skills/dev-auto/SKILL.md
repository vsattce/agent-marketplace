---
name: dev-auto
description: 自动准备与委派开发：仅在用户明确调用时，复用准备流程生成 SPEC / PLAN，自动检查后直接执行 SDD，普通需求无需确认；适用于 Codex、Claude Code、agy 和 dsh 桌面版。
disable-model-invocation: true
---

# 自动准备与委派开发

Only use when explicitly invoked by the user. Codex 使用 `$personal-dev:dev-auto`，Claude Code 使用 `/personal-dev:dev-auto`，agy / dsh 桌面版使用 `/dev-auto`；`$dev-auto` 是本文的入口简称。显式调用本入口即授权本次准备与委派组合流程，普通开发请求不自动触发。

1. 读取[准备与消费契约](../../references/preparation.md)，以 **auto 模式**执行 dev-prepare 等价流程：读取用户需求、项目规则和相关代码，生成文件形式的 SPEC / PLAN，自动检查需求、依赖、范围、验收及风险。
2. 无重大问题时记为 AUTO_READY，**不确认 SPEC、PLAN、模型或 effort，直接继续**。仅重大歧义、未授权的破坏性操作、安全边界不清允许集中询问一次；整次流程共用这一次预算，等待明确答复后继续，规则见共用契约。
3. 读取同包 [dev-delegate 执行正文](../dev-delegate/SKILL.md)，将生成的两个文件路径与 task-id 传入，在当前主控制上下文执行其完整 SDD 流程，直到整体检查与已有授权范围内的收尾结束。读取它引用的角色、修复收敛、ledger 和 Harness adapter 规则；**不在 Task 之间询问，不再做人工准备确认**。

组合通过读取共享文件执行，不要求客户端通过 Skill 工具嵌套调用手动入口，也不要求用户再发 dev-delegate 命令。dev-delegate 的显式授权条件由本次 dev-auto 调用满足；其他入口仍保持手动触发。**本文件不另行定义模型策略、修复轮次、调度或 Final Review 规则**，这些只维护在 dev-delegate 及其 references / scripts 中。

`SPEC > PLAN > Coder interpretation`。Coder / Reviewer 从文件读取既定需求；能力缺失或任务失败按既有执行契约报告，不能把受阻伪报完成。Git、发布、依赖和全局环境权限服从目标项目规则与本次已有授权。
