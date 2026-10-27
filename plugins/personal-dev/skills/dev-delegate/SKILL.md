---
name: dev-delegate
description: SPEC / PLAN 委派执行：仅在用户明确调用时，默认短路径完成开发、独立验收与必要修复，高风险按需升级；适用于 Codex、Claude Code、agy 和 dsh 桌面版。
disable-model-invocation: true
---

# 委派开发与独立验收

Only use when explicitly invoked by the user. Codex 使用 `$personal-dev:dev-delegate`，Claude Code 使用 `/personal-dev:dev-delegate`，agy / dsh 桌面版使用 `/dev-delegate`；`$dev-delegate` 是本文的入口简称。dev-auto 显式调用也授权读取本正文；普通请求不触发。

定位为轻量 SDD 执行器，只消费已确定的 SPEC / PLAN。`SPEC > PLAN > Coder interpretation`：SPEC 是业务需求最高约束，PLAN 冲突以 SPEC 为准，Coder / Reviewer 不重新解释明确需求。

默认路径：`worker → reviewer → 必要修复 → 最终 fresh verification → DONE`。简单任务直接走此路径；并行、ledger / 恢复、多轮修复、fresh coder、依赖冻结和 Final Reviewer 仅按下述实际需要启用。

## 1. 校验需求文件与委派能力

入口首先读取[子代理模型契约](../../references/subagent-models.md)，先归一化固定别名，再校验本次显式 `worker=<model>:<effort> reviewer=<model>:<effort>` 及 Harness 能力；缺任一参数立即中断，列出缺项和正确格式。此检查早于读取需求文件和任何写入，不使用默认值。

确认 Harness 与项目规则。Codex 读取 [Codex](../../references/codex.md)，用 `scripts/select_models.py` 校验；Claude Code 读取 [Claude](../../references/claude.md)，agy 读取 [agy](../../references/agy.md)，dsh 读取 [dsh](../../references/dsh.md)，按原生 schema 落实配置，不运行 Codex helper。未知 Harness、缺少委派、配置覆写或干净上下文时 BLOCKED，不安装、改全局配置或由主模型接手编码绕过。

先读取[准备与消费契约的执行入口](../../references/preparation.md#执行入口查找与校验)，定位 SPEC / PLAN，核对项目、就绪状态与任务。文件缺失时提示 `$dev-prepare` 或 `$dev-auto` 的客户端完整调用名，列缺项并结束；**不重新推导业务需求或生成另一套定义**。PLAN 局部错误按 SPEC 裁决并记录；重大缺口报告。

## 2. 展示已验证的显式配置

仅用显式 worker / reviewer；不支持即中断，不自动选型、推断 effort 或 fallback，主模型不变。

派发前展示已验证配置，例如：

```text
worker 模型：gpt-6-luna｜思考强度：high
reviewer 模型：gpt-6.1-terra｜思考强度：high
```

示例不作默认。执行型用 worker；判断型（含复验、Final Reviewer）用 reviewer。**展示后直接执行，不在 Task 间询问。**

## 3. 按 PLAN 派发

沿用 PLAN 的任务、依赖、write_scope、验证与完成标准，不重新拆解业务。派发前读取[角色契约](references/roles.md)，复杂 / 高风险任务按编排参考预检。新 Coder 使用干净上下文，只传项目、SPEC / PLAN 定位、规则、必要接口和基线，不复制聊天或全文；子代理禁止派生代理、commit / push。

默认精简交接，无 ledger 或长报告。仅任务确需并行调度、长时恢复、复杂依赖或只读计划裁决记录时，读取[任务编排与进度恢复](references/orchestration.md)，按同一 task-id 创建被 Git 忽略的 progress.md；普通少量串行任务可在可写 PLAN 简记进度。恢复核对文件、代码、Git 和代理状态，不重复派发、不清零计数。产物位置见[共用约定](../../references/artifacts.md)。

默认一个 worker 顺序执行；多个独立任务确有并行收益或用户要求时，再按编排契约核对范围、资源与槽位，最多三个写代理。PLAN 的 can_parallel 只是候选资格。下游须等上游独立验收通过且契约确定；冲突或并发能力不明时串行，派发时简述理由。

保留原有 tracked / staged / untracked 改动。验收覆盖任务的暂存、未暂存和新文件，不能仅用 BASE..HEAD。无法区分已有改动时核对边界，不重置或丢弃；无法安全执行则阻塞受影响任务。

## 4. 独立验收与必要修复

Coder 自检后，由主模型派发区别于全部 Coder 的干净只读 Reviewer。Reviewer 读取同一 SPEC / PLAN 与实际改动、报告、验证证据，检查需求、正确性、直接调用关系与必要质量边界。验收前确认 worker 已停止该范围写入；仅存在并发写入或变化中的依赖风险时冻结相关范围，无关安全任务可继续。Coder / Reviewer 不直接讨论，主模型传递必要信息。

按 [修复与收敛契约](references/roles.md#修复与收敛) 分类和裁决 finding：有依据的真实 blocker 才进入修复；重复问题沿用 ID，普通建议、样式偏好不阻塞，超出 SPEC 的要求拒绝并说明。必要验收证据未验证不能伪报 PASS。

无 blocker 直接进入最终核验；通常有 blocker 时由原 Coder 修一次并独立复验，通过即结束修复。**初次实现不计；一次修复加一次独立复验为一轮，每任务最多 3 轮，上限不是默认流程。** 只有真实 blocker 持续存在才进入下一轮；仅原代理不可恢复、上下文失效或同根因反复无进展时启用 fresh coder，不按轮次机械换人，始终使用同一 worker 配置与 SPEC / PLAN。复验聚焦原问题、修复和直接影响。

第三轮后主模型逐项 adjudication / convergence，核对证据与剩余 blocker，不因新增 finding 重开预算，不允许第四轮或把核心缺陷降为通过。核心 blocker 未解则该任务 FAILED，仅冻结依赖链及具体风险影响范围，其他安全任务继续；只有风险覆盖所有剩余路径或必需能力整体不可用才全局停止。

有 ledger 时修复派发前预记 fix_rounds 与 FIXING，返回记 REVIEW；同轮复验不加一。换代理、改名、恢复和最终检查均不重置预算。失败、中断或未完成项保留文件和 ledger。

## 5. 主模型整体检查与条件 Final Reviewer

可执行任务处理完后，主模型**始终做一次整体检查与最终 fresh verification**，即使存在 FAILED / BLOCKED 项：对照 SPEC 核对总需求、跨任务行为、范围、累计差异，在最后修改后运行最小有效验证并核对结果，再报告 DONE；无后续变化的当前轮实测可复用，不重复全量验证。单任务聚焦需求、范围和最终版本，不能只凭旧报告宣称通过。终审发现问题交 Coder，沿用所属任务剩余修复预算；同一缺陷不能改名为新任务获新预算。

额外独立 Final Reviewer **仅以下情况默认触发**：用户明确要求；安全 / 权限相关；并发 / 事务一致性；破坏性数据迁移；明显的公共 API 不兼容风险。代码多、任务多、复杂度高本身不触发；普通页面、样式、常规前后端联调、兼容性 API 增加和一般功能默认仅由主模型整体检查。

触发时使用同一 reviewer 配置，不另行选型或升降 effort；另建区别于全部 Coder 和任务 Reviewer 的只读上下文，检查整体契约与触发风险，沿用同一 SPEC、finding 分类和修复预算，不启动 dev-review 全项目流程。结果交主模型裁决后汇总。

最终报告 DONE、FAILED、依赖 BLOCKED、风险冻结项、验证及未验证项。部分失败保留成果与记录，不宣称全部完成，不自动提交 / 推送 / 发布混合的失败实现。全部通过后按目标项目已有授权收尾，不增加 Git、发布或全局写入权限。简短汇报进度；清理仅限已完成并核实路径的本次临时目录。
