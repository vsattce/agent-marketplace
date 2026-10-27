# Claude Code 委派适配

仅用于已确认的 Claude Code Harness。入口首先遵守[子代理模型契约](subagent-models.md)，校验本次显式 worker / reviewer。主会话模型与用户配置保持原样；不运行 Codex Python helper。

## 显式模型与思考配置

从本轮原生 Agent schema、可用型号与每个型号的 effort 支持证据，核验两类配置。执行型子代理使用 worker，审查、SPEC / PLAN 符合性、验证结果、回归风险、独立复核与 Final Reviewer 使用 reviewer。每次 Agent 都必须显式传该角色的 model 和当前 schema 实际支持的 effort 覆写字段，不能省略或通过提示正文声称已应用。

Claude 的 effort 不等于 Codex reasoning_effort；若本轮 Agent 只有 model、没有可核验的 effort 覆写能力，立即 BLOCKED，明确说明当前工具无法落实用户指定强度。模型不可用、不支持所请求 effort、名单或生效证据缺失、managed 策略会替换指定值时同样中断。不沿用原生默认、不标 UNKNOWN 后继续，不改环境变量、项目或用户设置来补能力。

成功时展示已验证 worker / reviewer 两行。多个执行代理共享 worker，多个审查代理共享 reviewer。第三轮 fresh coder 使用同一 worker；Final Reviewer 使用同一 reviewer，不独立选型或升降强度。继续原代理前核对配置一致，不能假设恢复时可以改参数；不一致或无法核验时停止续接并报告。权限、只读、独立上下文与三轮修复预算不变。

## 原生委派

1. 确认本轮 `Agent` 与通用子代理可用。优先当前声明支持的 `subagent_type: "general-purpose"`；无此类型时只能选择经本轮证实具有所需读写或审查能力的通用类型，否则 `BLOCKED`。不用只读 Explore / Plan 代理编码。
2. 新任务和独立验收使用不同的新代理，提供精简任务提示与项目规则，不复制完整聊天。选择通用非 fork 子代理；若当前接口显式提供 fork 开关，按其 schema 关闭，不猜不存在的参数，不使用继承整段历史的 fork 代替独立上下文。只读验收 / 审查提示明确禁止写文件、修复、提交、派生代理与运行有副作用命令。
3. `dev-delegate` 按共享编排自动识别独立任务，满足条件默认两个编码代理并行，有依赖、冲突或并发能力缺失 / 不明时串行。只用本轮明确支持的原生并发调用或后台执行，先启动本批任务再等待结果；工作区与实际槽位须安全，不启用 Agent Teams。验收另开独立代理。记录工具返回的代理 ID / 任务 ID；多任务同步写回 ledger。前台调用等待返回；后台任务按本轮原生完成通知或 task-output 接口读取结果，不按 Codex 工具名轮询。
4. 原编码代理返工使用当前支持的原生继续方式。提供 `SendMessage` 时按真实 schema 将代理 ID 作为 `to`，否则只有当前 `Agent` 声明支持 `resume` 时才使用它；两者都不支持或 dev-delegate 第三轮使用 fresh coder 时重建精简上下文。不要向其他用户聊天发消息，不假设恢复时可以改变型号 / 思考配置。累计修复次数不清零。
5. 缺失委派、独立上下文或必要权限时集中 `BLOCKED`，报告已有工作；不嵌套启动 `claude -p`、不启用 agent teams、不安装依赖或修改权限来补能力。

依据：[Claude Code subagents](https://code.claude.com/docs/en/sub-agents)、[Skills 与手动调用](https://code.claude.com/docs/en/skills)。开发验证与实际业务执行分别记录；隔离捕获加载请求不代表已执行真实模型委派。

`dev-delegate` 第三轮使用 fresh coder 和同一 worker；独立 Final Reviewer 按主 Skill 条件触发并使用同一 reviewer。主模型始终做整体检查，不能用额外 Reviewer 取代。
