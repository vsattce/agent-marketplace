# Codex 委派适配

仅用于已确认的 Codex Harness。共享流程见对应 Skill；本文件处理模型选择与原生工具，Claude Code 不执行这里的 Python 检查器。

## 模型与显示

主模型身份仅取本轮可靠运行时信息或用户明确说明；自报身份、默认配置、历史会话与记忆不是本轮身份依据。根据当前派发工具声明整理实际模型 ID 与支持强度；网页、模型目录和缓存不能替代当前允许名单。

通过当前 Skill 的 `scripts/select_models.py` 校验输入，使用已有且符合环境规则的 Agent 工具 Python，不安装依赖、不修改目标项目运行时、PATH 或全局配置。解释器缺失时 `BLOCKED`。检查器只验证传入模型元数据，不发现模型、不验证来源真实性、不拦截原生派发。

JSON stdin 必填 `primary_model`、`primary_model_source`（`current-turn` / `user`）、`inventory_source`（`current-spawn-tool`）、`models`（每项含 `id` 和 `efforts` 数组）。开发默认 `coding_effort=high` / `review_effort=xhigh`，审查默认 `audit_effort=xhigh` / `verification_effort=max`。用户明确指定某角色的强度时传对应字段，未指定的角色使用默认值；例如“编码 medium，验收 xhigh”传 `coding_effort=medium` / `review_effort=xhigh`。这已是本次强度覆写要求，无需再次确认；仍须校验当前工具支持，不支持则说明原因并 `BLOCKED`。输入不含任务秘密。退出 0 且 `READY` 才可派发；退出 2 或 `BLOCKED` 时停止。

- 已确认的低成本系列为 `gpt-<数字版本>-luna`，选主模型同一大版本内数值最高的可用版本。6.1 / 6.2 主模型可用 6 Luna；7 主模型不能自动回退 6 或 5.6。
- 开发默认编码 `high`、独立验收 `xhigh`；增强审查默认审查 `xhigh`、复核 `max`（最强）。用户指定的强度优先，两个角色使用同一实际型号。最高版本缺少所需强度、身份或名单缺失、版本多 ID 歧义、工具不能覆写时 `BLOCKED`；不能自行改用较旧版本、降低强度或由主模型代做。
- 陌生系列或改名时查官方定位与替代关系，给出不确定项并等用户决定，不按 `mini` / `lite`、价格或推荐猜测。
- 用户明确确认当前任务的精确替代型号后，才传 `model_override` 和 `override_confirmed: true`；仍检查实际名单与强度。持久修改系列策略需要另行授权。

派发前原样展示 helper 的 `display` 两行实际结果。开发为“编码模型 / 验收模型”，审查为“审查模型 / 复核模型”；型号或强度变化时重新展示。

## dev-delegate 的独立整体终审

编码与任务验收保持上述默认和覆写规则。复杂任务先由主模型补齐设计、接口与可验证条件；默认模型仍不足时说明具体能力缺口与建议的精确替代型号，已有授权则校验执行，否则等待用户决定，不自动跨系列升级。

仅按主 Skill 的风险条件触发整体终审。上限取本轮会话已确认的精确型号和实际思考强度；两者只能来自本轮可靠运行时信息或用户明确说明，不能用默认配置、历史值或工具可选最高档代替当前选择。终审固定使用该型号，避免按名称猜测跨型号强弱。

触发时给 `dev-delegate/scripts/select_models.py` 的既有输入增加 `final_review_required: true`、`primary_effort`、`primary_effort_source`（`current-turn` / `user`），初派省略 `final_review_escalated` 或传 `false`。脚本返回 `final_review`，默认比会话低一档；紧邻档位不可用时只能再降低，已在最低档时沿用最低档，无可用低档则 `BLOCKED`。例如会话 `high` → 终审 `medium`，会话 `ultra` → 终审 `max`。不触发终审时不传这些新增元数据，原编码 / 任务验收接口与默认值保持不变。

符合角色契约中的困难升级条件时，主模型先记录升级已使用，再重新核验当前会话上限，传 `final_review_escalated: true` 重跑脚本；仅返回同型号、与当前会话相同的强度。上限档不可派发、无更高空间或已升级过时停止，不绕过检查选其他档。派发原样使用 `final_review` 并展示脚本的终审行及会话上限；切换会话型号 / 强度、恢复或升级前重新核验，旧记录不能授权更高设置。原生接口不能原地改变强度时，结束旧终审后新建同型号的干净终审代理，只交接问题、证据和已用升级状态。

缺少可靠的当前型号 / 强度、型号不可派发或工具不能落实所选强度时集中 `BLOCKED`，不自行取最高档或改配置兜底。脚本只校验调用者提供的元数据；主模型仍须保证来源真实、遵守一次升级限制，并在原生派发中使用校验结果。

## 派发与继续

以本轮工具声明为准，使用原生 `spawn_agent`，显式传校验结果的 `model` 与 `reasoning_effort`；新代理使用干净上下文，支持 `fork_turns` 时传 `"none"`。没有所需能力则 `BLOCKED`，不嵌套启动 Codex CLI。

V2 原编码代理返工优先用 `followup_task`，运行中补充信息可用 `send_message`；V1 或其他接口按实际声明使用 resume / follow-up，不编造参数。等待、状态和中断分别用当前可用的 wait / list / interrupt 工具。代理无法恢复时才重建任务上下文，累计修复次数不清零。不得用 Codex 聊天管理工具创建用户可见的新聊天来替代子代理。

`dev-delegate` 的有限并行仅使用本轮已确认的原生并发能力和实际槽位；缺失或不明则串行，不改配置补能力。多任务将工具返回的 Agent/task id、实际模型与强度、阶段及轮次写回 ledger；恢复先核对当前代理状态，不能因通知延迟再派发重叠写代理。模型选择与覆写策略保持不变。

当前 CLI 包装与加载证据记在 [维护指南](../../../docs/maintenance.md)；实际模型权限、额度与委派接口仍按本轮工具核对。
