---
name: dev-delegate
description: SPEC / PLAN 委派执行：仅在用户明确调用时，消费既定需求文件执行 SDD、独立验收与有限修复，支持依赖隔离和进度恢复；适用于 Codex、Claude Code、agy 和 dsh 桌面版。
disable-model-invocation: true
---

# 委派开发与独立验收

Only use when explicitly invoked by the user. Codex 使用 `$personal-dev:dev-delegate`，Claude Code 使用 `/personal-dev:dev-delegate`，agy / dsh 桌面版使用 `/dev-delegate`；`$dev-delegate` 是本文的入口简称。dev-auto 显式调用也授权读取本正文；普通请求不触发。

定位为轻量 SDD 执行器，只消费已确定的 SPEC / PLAN。`SPEC > PLAN > Coder interpretation`：SPEC 是业务需求最高约束，PLAN 冲突以 SPEC 为准，Coder / Reviewer 不重新解释明确需求。

## 1. 校验需求文件与委派能力

入口首先读取[子代理模型契约](../../references/subagent-models.md)，先归一化固定别名，再校验本次显式 `worker=<model>:<effort> reviewer=<model>:<effort>` 及 Harness 能力；缺任一参数立即中断，列出缺项和正确格式。此检查早于读取需求文件和任何写入，不使用默认值。

确认 Harness 与项目规则。Codex 读取 [Codex](../../references/codex.md)，用 `scripts/select_models.py` 核验工具、型号与强度；Claude Code 读取 [Claude](../../references/claude.md)，agy 读取 [agy](../../references/agy.md)，dsh 桌面版读取 [dsh](../../references/dsh.md)；后三者按原生 schema 落实同一 worker / reviewer，不运行 Codex helper。未知 Harness、缺少委派、配置覆写或干净上下文时报告具体 BLOCKED，不安装、改全局配置或由主模型接手编码绕过。

先读取[准备与消费契约的执行入口](../../references/preparation.md#执行入口查找与校验)，定位并读取 SPEC / PLAN 文件，核对项目、就绪状态与任务信息。找不到可用文件时明确提示 `$dev-prepare` 或 `$dev-auto`（使用客户端完整调用名），列出缺项并结束；**不从自然语言重新推导业务需求或生成另一套定义**。PLAN 局部错误由主模型按 SPEC 裁决，记录依据；重大缺口保留并报告。

## 2. 展示已验证的显式配置

仅用显式 worker / reviewer；不支持即中断，不自动选型、推断 effort 或 fallback，主模型不变。

派发前展示已验证配置，例如：

```text
worker 模型：gpt-6-luna｜思考强度：high
reviewer 模型：gpt-6.1-terra｜思考强度：high
```

示例不作默认。执行型用 worker；判断型（含复验、Final Reviewer）用 reviewer。**展示后直接执行，不在 Task 间询问。**

## 3. 按 PLAN 派发

沿用 PLAN 的任务、依赖、write_scope、验证与完成标准，不重新拆解业务。同一功能优先一个任务；局部计划错误按 SPEC 裁决。派发前读取[角色契约](references/roles.md)，复杂 / 高风险单任务也按编排参考做冲突预检。新 Coder 使用干净上下文，只传项目、SPEC / PLAN 路径与任务定位、规则、必要接口和基线，不复制聊天或全文；子代理禁止派生代理、commit / push。

单任务默认精简交接，无 ledger 或长报告；只读计划需裁决记录时按共用契约处理。两个及以上开发任务（含串行依赖）在首次派发前读取[任务编排与进度恢复](references/orchestration.md)，按同一 task-id 在隐藏执行目录创建被 Git 忽略的 progress.md；记录文件路径、依赖、状态、实际代理 / 模型、修复轮次和证据。恢复核对文件、代码、Git 和代理状态，不重复派发、不清零计数。产物位置见[共用约定](../../references/artifacts.md)。

按编排契约自动识别独立任务，满足安全条件默认两个写代理并行、最多三个；已有 PLAN 缺少标记时也自动判断，显式串行要求保留。下游须等上游独立验收通过且契约确定；冲突或并发能力不明时串行，派发时简述理由。

记录并保留原有 tracked / staged / untracked 改动。验收覆盖任务的暂存、未暂存和新文件，不能仅用 BASE..HEAD 代替未提交差异。无法区分已有改动时先按证据确定边界，不重置或丢弃；确实无法安全执行则冻结受影响任务。

## 4. 独立验收、最多三轮修复与收敛

Coder 自检后，由主模型派发区别于全部 Coder 的干净只读 Reviewer。Reviewer 读取同一 SPEC / PLAN 与实际改动、报告、验证证据，检查需求、正确性、直接调用关系与必要质量边界。验收期间冻结该范围及相关依赖写入；无关安全任务可继续。Coder / Reviewer 不直接讨论，主模型传递必要信息。

按 [修复与收敛契约](references/roles.md#修复与收敛) 分类和裁决 finding：有依据的真实 blocker 才进入修复；重复问题沿用 ID，普通建议、样式偏好不阻塞，超出 SPEC 的要求拒绝并说明。必要验收证据未验证不能伪报 PASS。

**初次实现不计；一次修复加一次独立复验为一轮，每任务最多 3 个修复轮次。** Round 1 / 2 优先原 Coder；Round 3 仍有真实 blocker 时使用 fresh coder，仍使用同一 worker 配置；交接同一 SPEC、PLAN、当前实现、blocker 与历史尝试，不重新理解业务。复验聚焦原问题、修复和直接影响。

第三轮后主模型逐项 adjudication / convergence：区分真实 / 重复 blocker、新发现、非阻塞建议、偏好和范围外要求，记录证据与裁决。不因新增 finding 重开预算，不允许第四轮或把核心缺陷降为通过。仍有无法解决的核心 blocker 则记该任务 FAILED，仅冻结依赖链及具体受风险影响的任务；其他无依赖安全任务继续。全局停止仅用于风险确实覆盖所有剩余路径或必需执行能力整体不可用，不能因单任务失败默认全停。

有 ledger 时修复派发前预记 fix_rounds 与 FIXING，返回记 REVIEW；同轮复验不加一。换代理、改名、恢复和最终检查均不重置预算。失败、中断或未完成项保留文件和 ledger。

## 5. 主模型整体检查与条件 Final Reviewer

可执行任务处理完后，主模型**始终做一次整体检查**，即使存在 FAILED / BLOCKED 项：对照 SPEC 核对总需求、跨任务行为、范围、累计差异和证据对应的最终版本。复用已验收内部结论，只复核具体疑点与后续变化；单任务核对需求、范围和版本。终审发现问题交 Coder，沿用所属任务剩余修复预算；同一缺陷不能改名为新任务获新预算。

额外独立 Final Reviewer **仅以下情况默认触发**：用户明确要求；安全 / 权限相关；并发 / 事务一致性；破坏性数据迁移；明显的公共 API 不兼容风险。代码多、任务多、复杂度高本身不触发；普通页面、样式、常规前后端联调、兼容性 API 增加和一般功能默认仅由主模型整体检查。

触发时使用同一 reviewer 配置，不另行选型或升降 effort；另建区别于全部 Coder 和任务 Reviewer 的只读上下文，检查整体契约与触发风险，沿用同一 SPEC、finding 分类和修复预算，不启动 dev-review 全项目流程。结果交主模型裁决后汇总。

最终如实报告 DONE、FAILED、依赖 BLOCKED、风险冻结项、验证及未验证项。部分失败时不得宣称全部完成，也不自动提交 / 推送 / 发布混合的失败实现；保留成果与记录。全部通过后按目标项目已有授权与规则执行收尾，本 Skill 不额外授予 Git、发布或全局写入权限。定期简短汇报进度；清理只针对已完成并核实路径的本次临时目录。
