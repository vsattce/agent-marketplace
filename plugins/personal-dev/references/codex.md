# Codex 委派适配

仅用于已确认的 Codex Harness。入口首先遵守[子代理模型契约](subagent-models.md)，同时校验显式 worker / reviewer；主会话模型保持用户原本选择，不取主模型身份或 effort 来选子代理。

## 模型校验与显示

根据本轮派发工具声明整理实际模型 ID 与各型号支持的 effort。网页、缓存和默认配置不能替代当前允许名单；工具不支持显式覆写模型或 reasoning_effort 时立即 BLOCKED。

使用共享 `skills/dev-delegate/scripts/select_models.py`，dev-review 的同名 helper 仅透传同一协议。JSON 必填 worker、reviewer（各为 `<model>:<effort>` 字符串）、inventory_source=current-spawn-tool、models（每项含 id 与 efforts）。省略字面 gpt- 前缀只能精确唯一匹配，不排序或自动挑型号；不接受主模型、旧角色与终审专用参数。

用符合环境规则的现有 Python，不安装依赖、不修改目标项目运行时、PATH 或全局配置。解释器缺失时 BLOCKED。退出 0 且 READY 才能派发，原样展示返回的 worker / reviewer 两行 display；退出 2 或 BLOCKED 立即停止，不补默认值或换配置。helper 只校验元数据，不能代替主模型核验来源或落实派发。

## 所有角色的原生参数

执行型（Coder、搜索/文件读取、引用查询、命令、配置、补测试和修复）均取结果 `worker`；判断型（代码审查、SPEC / PLAN 检查、验证结果检查、回归风险、独立验收、复验、Final Reviewer）均取结果 `reviewer`。每次原生 spawn 都显式传：

```text
model = result[role]["model"]
reasoning_effort = result[role]["effort"]
fork_turns = "none"
```

其中 role 只能是 worker 或 reviewer。多个并行 Worker 使用同一 worker；多个 Reviewer 使用同一 reviewer。role 是配置键，不猜造原生 agent_type。需要覆写时使用干净上下文；当前工具不支持这些必要参数或独立上下文则 BLOCKED。原生拒绝请求或实际返回配置不一致立即停止，不忽略参数、不降低 effort、不继承主模型、不嵌套 Codex CLI。

Final Reviewer 仅按主 Skill 条件启动，固定使用同一 reviewer，不做会话低一档或思考升级。第三轮 fresh coder 固定使用同一 worker。继续原代理前核对已有配置与本次显式配置一致；无法确认或不一致就停止续接并说明，不能默认沿用。新建代理仍保留修复计数与证据。

## 派发与继续

以本轮工具声明为准，使用原生 `spawn_agent`，显式传校验结果的 `model` 与 `reasoning_effort`；新代理使用干净上下文，支持 `fork_turns` 时传 `"none"`。没有所需能力则 `BLOCKED`，不嵌套启动 Codex CLI。

V2 原编码代理返工优先用 `followup_task`，运行中补充信息可用 `send_message`；V1 或其他接口按实际声明使用 resume / follow-up，不编造参数。等待、状态和中断分别用当前可用的 wait / list / interrupt 工具。代理无法恢复或 dev-delegate 第三轮使用 fresh coder 时重建精简上下文，累计修复次数不清零。不得用 Codex 聊天管理工具创建用户可见的新聊天来替代子代理。

`dev-delegate` 按共享编排自动识别独立任务，满足条件默认两个编码代理并行；先用原生工具启动本批任务，再等待结果。有依赖、冲突或并发能力缺失 / 不明时串行，仅使用本轮已确认的原生能力和实际槽位，不改配置补能力。多任务将工具返回的 Agent/task id、实际模型与强度、阶段及轮次写回 ledger；恢复先核对当前代理状态，不能因通知延迟再派发重叠写代理。模型选择与覆写策略保持不变。

当前 CLI 包装与加载证据记在 [维护指南](../../../docs/maintenance.md)；实际模型权限、额度与委派接口仍按本轮工具核对。

## dev-delegate 的第三轮

第三轮 fresh coder 使用同一 worker 配置；复验和 Final Reviewer 使用同一 reviewer，不自动改变模型或 effort。
