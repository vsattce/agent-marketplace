---
name: dev-delegate
description: SPEC / PLAN 委派执行：仅在用户明确调用时，默认短路径完成开发、独立验收与必要修复，高风险按需升级；适用于 Codex、Claude Code、agy 和 dsh 桌面版。
disable-model-invocation: true
---

# 委派开发与独立验收

仅用户显式调用时使用：Codex 为 `$personal-dev:dev-delegate`，Claude Code 为 `/personal-dev:dev-delegate`，agy / dsh 为 `/dev-delegate`；下文简称 `$dev-delegate`。显式 dev-auto 也授权读取本正文，普通请求不触发。

只消费已确定的 SPEC / PLAN，遵守 `SPEC > PLAN > Coder interpretation`；所有角色不重新解释明确需求。

默认路径：`worker → reviewer → 必要修复 → 最终 fresh verification → DONE`；并行、ledger / 恢复、多轮修复、fresh coder、依赖冻结和 Final Reviewer 均按需启用。

## 1. 校验需求文件与委派能力

入口首先读取[子代理模型契约](../../references/subagent-models.md)，按共享规则校验本次显式 `worker=<model>:<effort> reviewer=<model>:<effort>`，接受 `w 6luna high r 6.1terra high` 等简写，先归一化再校验，不因空格或省略连字符拒绝含义明确的输入。缺任一参数立即中断，列出缺项和规范格式；模型与 Harness 校验须早于需求文件读取和任何写入。

确认项目规则与实际 Harness，读取对应 adapter：[Codex](../../references/codex.md)、[Claude](../../references/claude.md)、[agy](../../references/agy.md) 或 [dsh](../../references/dsh.md)。未知 Harness、缺少委派、配置覆写或干净上下文时 BLOCKED，不安装、改全局配置或由主模型接手编码绕过。

先读取[准备与消费契约的执行入口](../../references/preparation.md#执行入口查找与校验)，定位 SPEC / PLAN，核对项目、就绪状态与任务。缺文件时列缺项，提示 `$dev-prepare` / `$dev-auto` 的客户端完整调用名并结束，不重建业务定义。PLAN 局部错误按 SPEC 裁决并记录，重大缺口报告。

## 2. 展示已验证的显式配置

按模型契约展示实际配置：`worker 模型：<实际 ID>｜思考强度：<effort>`、`reviewer 模型：<实际 ID>｜思考强度：<effort>`。执行型用 worker，判断型用 reviewer；**展示后直接执行，不在 Task 间询问。**

## 3. 按 PLAN 派发

沿用 PLAN 的任务、依赖、write_scope、验证与完成标准。派发前必读[角色契约](references/roles.md)；执行命令前读取[命令与资源契约](../../references/execution-resources.md)，交接须覆盖未退出的验证命令。

默认一个 worker 顺序执行，精简交接，普通少量串行任务在可写 PLAN 简记进度，无需 ledger 或长报告。仅确需并行调度、长时恢复、复杂依赖或只读计划裁决记录时建立被 Git 忽略的同一 task-id progress.md；产物位置见[共用约定](../../references/artifacts.md)。

复杂 / 高风险预检、并行、ledger / 恢复或依赖风险隔离触发时，先读[任务编排与进度恢复](references/orchestration.md)。多个独立任务确有并行收益或用户要求且安全条件满足时才并行，最多三个写代理；can_parallel 仅为候选。下游等上游独立验收通过且契约确定，冲突或并发能力不明时串行，派发时简述理由。

保留用户原有 tracked / staged / untracked 改动；验收覆盖任务的全部差异，不能仅用 BASE..HEAD。归属不明先核对边界，不重置或丢弃；无法安全执行则阻塞受影响任务。

## 4. 独立验收与必要修复

Coder 自检后，由区别于全部 Coder 的干净只读 Reviewer 独立验收。按角色契约核对当前代码与证据，主模型裁决 finding；只修真实 blocker，建议、偏好和范围外要求不延长循环，必要证据未验证不得报 PASS。

无 blocker 直接最终核验；通常有 blocker 时由原 Coder 修一次并独立复验，通过即结束。只有真实 blocker 持续存在才进入下一轮，每任务最多 3 轮，上限不是默认流程。计数、三轮后收敛、fresh coder 条件与失败隔离统一按[修复与收敛契约](references/roles.md#修复与收敛)，不重开预算、不按轮次机械换人。

## 5. 主模型整体检查与条件 Final Reviewer

可执行任务处理完后，主模型**始终做一次整体检查与最终 fresh verification**，包括存在 FAILED / BLOCKED 项时：对照 SPEC 核对总需求、跨任务行为、范围、累计差异及最终版本；最后修改后运行最小有效验证并核实结果。无后续变化的当前轮实测可复用，不重复全量验证或仅凭旧报告报 DONE；单任务聚焦需求、范围与最终版本。

风险终审 **仅以下情况默认触发**：用户明确要求；安全 / 权限；并发 / 事务一致性；破坏性数据迁移；明显的公共 API 不兼容风险。代码量、任务数、复杂度本身不触发，普通页面、样式、常规联调、兼容性 API 增加与一般功能由主模型整体检查。

触发时按角色契约检查风险覆盖；单个完整验收单元可复用已覆盖这些风险的当前独立验收，仅有具体缺口或用户明确要求另一位终审者才增加 Final Reviewer。沿用同一 SPEC 和任务剩余修复预算，不启动另一套全项目审查。

最终简报 DONE、FAILED、依赖 BLOCKED、风险冻结项、验证与未验证项。部分失败保留成果及记录，不报全部完成，不自动提交 / 推送 / 发布混合的失败实现。全部通过后按目标项目已有授权收尾；清理仅限已完成并核实路径的本次临时目录，不增加 Git、发布或全局写入权限。
