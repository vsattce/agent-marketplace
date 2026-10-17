# Codex 委派适配

仅用于已确认的 Codex Harness。共享流程见对应 Skill；本文件处理模型选择与原生工具，Claude Code 不执行这里的 Python 检查器。

## 模型与显示

主模型身份仅取本轮可靠运行时信息或用户明确说明；自报身份、默认配置、历史会话与记忆不是本轮身份依据。根据当前派发工具声明整理实际模型 ID 与支持强度；网页、模型目录和缓存不能替代当前允许名单。

通过当前 Skill 的 `scripts/select_models.py` 校验输入，使用已有且符合环境规则的 Agent 工具 Python，不安装依赖、不修改目标项目运行时、PATH 或全局配置。解释器缺失时 `BLOCKED`。检查器只验证传入模型元数据，不发现模型、不验证来源真实性、不拦截原生派发。

JSON stdin 必填 `primary_model`、`primary_model_source`（`current-turn` / `user`）、`inventory_source`（`current-spawn-tool`）、`models`（每项含 `id` 和 `efforts` 数组）。开发默认 `coding_effort=high` / `review_effort=xhigh`，审查默认 `audit_effort=xhigh` / `verification_effort=max`。用户明确指定某角色的强度时传对应字段，未指定的角色使用默认值；例如“编码 medium，验收 xhigh”传 `coding_effort=medium` / `review_effort=xhigh`。这已是本次强度覆写要求，无需再次确认；仍须校验当前工具支持，不支持则说明原因并 `BLOCKED`。输入不含任务秘密。退出 0 且 `READY` 才可派发；退出 2 或 `BLOCKED` 时停止。

- 已确认的低成本系列为 `gpt-<数字版本>-luna`，选主模型同一大版本内数值最高的可用版本。6.1 / 6.2 主模型可用 6 Luna；7 主模型不能自动回退 6 或 5.6。
- 开发默认编码 `high`、独立验收 `xhigh`；增强审查默认审查 `xhigh`、复核 `max`（最强）。用户指定的强度优先，两个角色使用同一实际型号。最高版本缺少所需强度、身份或名单缺失、版本多 ID 歧义、工具不能覆写时 `BLOCKED`；不能自行改用较旧版本、降低强度或由主模型代做。
- 陌生系列或改名时查官方定位与替代关系，不按 `mini` / `lite`、价格或推荐猜测。dev-delegate（含 dev-auto）不能据现有规则安全选型时报告具体能力限制，不追加型号确认；dev-review 沿用其显式覆写边界。
- 用户明确指定当前任务的精确替代型号即构成覆写授权，直接传 `model_override` 和 `override_confirmed: true`；该字段记录已有授权，不再提问确认。仍检查实际名单与强度。持久修改系列策略需要另行授权。

派发前原样展示 helper 的 `display` 两行实际结果。开发为“编码模型 / 验收模型”，审查为“审查模型 / 复核模型”；型号或强度变化时重新展示。

## dev-delegate 的独立整体终审

只有主 Skill 的五类条件触发才派独立 Final Reviewer，不因规模或一般复杂度触发。预检从现成 SPEC / PLAN 核对关键设计、接口和验证；普通计划缺陷按 SPEC 裁决，不重新推导需求，不因模型选项请求确认。

沿用同一 `dev-delegate/scripts/select_models.py`，触发时传 `final_review_required: true`，只使用返回的 `final_review` 派发并展示第三行。自动策略：本轮可信会话型号 / effort 可核验且能派发时，使用会话同型号、低一档 effort，紧邻档不可用只可更低；最低档沿用最低档。会话 effort 未公开时省略 primary_effort / primary_effort_source，或会话型号 / 低档不可派发时，自动沿用已验证的任务验收配置，如实展示该策略，不索取型号或 effort，也不把回退结果冒充满足无法核验的会话上限。实际委派 / 独立上下文能力缺失仍报告技术 BLOCKED。

已知当前 effort 时一并传 `primary_effort` 与 `primary_effort_source`（current-turn / user）；不传 UNKNOWN、历史值或工具最高可选档。用户明确指定最终审查型号 / effort 时，仅传其明确指定的 `final_review_model` / `final_review_effort`，用户指定优先，无二次确认；未指定的设置自动选择：只指定 effort 时沿用可派发的会话型号，否则任务验收型号；只指定型号时，同会话型号沿用低一档策略，其他型号优先任务验收 effort，缺档则取不高于该档的最高可用档。请求值不在当前名单或强度不受支持时说明技术限制，不默默忽略用户值。不触发终审时不传终审专用字段，编码 / 任务验收默认不变。

角色契约的困难条件成立且已有可信会话上限时，先记录唯一升级已用，再核验当前上限并传 `final_review_escalated: true`；同型号最高只升到当前会话强度，不能覆写用户明确终审配置。原生接口不能原地改强度时结束旧终审后新建干净代理，保留已用升级和代码修复次数。会话预算未知时保持已验证配置进行裁决，不为获取预算提问；确实无法形成必要结论时阻塞相关任务，不盲目加档。脚本只校验元数据，主模型负责来源真实性、一次升级限制和原生参数的实际使用。

## 派发与继续

以本轮工具声明为准，使用原生 `spawn_agent`，显式传校验结果的 `model` 与 `reasoning_effort`；新代理使用干净上下文，支持 `fork_turns` 时传 `"none"`。没有所需能力则 `BLOCKED`，不嵌套启动 Codex CLI。

V2 原编码代理返工优先用 `followup_task`，运行中补充信息可用 `send_message`；V1 或其他接口按实际声明使用 resume / follow-up，不编造参数。等待、状态和中断分别用当前可用的 wait / list / interrupt 工具。代理无法恢复或 dev-delegate 第三轮使用 fresh coder 时重建精简上下文，累计修复次数不清零。不得用 Codex 聊天管理工具创建用户可见的新聊天来替代子代理。

`dev-delegate` 按共享编排自动识别独立任务，满足条件默认两个编码代理并行；先用原生工具启动本批任务，再等待结果。有依赖、冲突或并发能力缺失 / 不明时串行，仅使用本轮已确认的原生能力和实际槽位，不改配置补能力。多任务将工具返回的 Agent/task id、实际模型与强度、阶段及轮次写回 ledger；恢复先核对当前代理状态，不能因通知延迟再派发重叠写代理。模型选择与覆写策略保持不变。

当前 CLI 包装与加载证据记在 [维护指南](../../../docs/maintenance.md)；实际模型权限、额度与委派接口仍按本轮工具核对。

## dev-delegate 的第三轮

第三轮默认 fresh coder 使用已验证编码配置；需要提升且用户未指定该角色 effort 时，可用同一 helper 校验更高的当前支持强度再派发，不绕过同代策略或猜测更强型号。已有用户覆写优先。型号 / 强度变化展示后继续，不询问。
