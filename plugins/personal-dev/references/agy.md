# Antigravity CLI（agy）委派适配

仅用于确认当前 Harness 为 Antigravity CLI 的会话，不能从 Gemini 模型名推断客户端。共享需求、角色、修复轮次及终审条件保持不变，不执行 Codex 的 Python 选型器。

入口首先遵守[子代理模型契约](subagent-models.md)，同时校验本次显式 worker / reviewer；主会话模型不变。

## 原生模型与委派

1. 以本轮实际工具 schema 为准，确认 `invoke_subagent`、独立上下文及完成结果读取能力。优先使用具备所需工具的原生 `self` 或当前已发现的通用子代理；`research` 等只读角色不能编码。缺少必要能力时报告具体 `BLOCKED`，不嵌套启动 `agy -p` 或其他客户端补能力。
2. 执行型子代理使用 worker；审查、SPEC / PLAN 检查、验证结果、回归风险、独立验收和复核使用 reviewer。按当前 invoke_subagent schema 显式传对应 model 与原生 effort 覆写字段，先核验名单与每个型号支持的强度并展示两类实际配置。没有可核验的覆写字段、模型不可用或 effort 不支持时立即 BLOCKED 并说明具体能力缺口；不继承原生默认、不以 UNKNOWN 继续、不套用其他客户端字段。多个 Worker 共享 worker，多个 Reviewer 共享 reviewer；原生拒绝或实际配置不一致时停止，不换配置。
3. 新任务和独立验收使用不同的干净子代理，只传任务、项目、SPEC / PLAN 路径、必要规则与证据。使用当前工作区的共享或继承模式，具体字段按 schema；不为普通任务自动创建分支或 worktree。按共享编排自动判断独立任务，原生并发能力与范围安全均已确认时默认两个编码代理并行，先启动本批再等待；依赖、冲突、能力不明或明确串行要求下使用单写。
4. 验收 / 审查提示明确只读，不修复、不提交、不派生代理。记录原生返回的 agent / conversation ID，按当前状态、结果和消息工具等待或继续；返工优先恢复原编码代理，第三轮按共享契约新建。恢复和重建不清零修复预算，不向其他用户聊天发消息。
5. 独立 Final Reviewer 仍只在主 Skill 的规定条件触发，使用同一 reviewer，不自动升降强度；第三轮 fresh coder 使用同一 worker。恢复原代理前核对配置一致，不一致或无法核验则停止续接并说明。三轮修复和主模型整体检查的边界保持不变，不修改用户配置。

## 调用与权限

agy 将 Skills 提供为 `/<skill-name>`，例如 `/dev-prepare`、`/dev-delegate`、`/dev-auto`、`/dev-review`、`/dev-simplify`、`/dev-runtime-check`。以当前会话实际展示的命令为准；这些入口仍仅在用户明确调用时执行，普通任务或提及名称不触发。保留 `disable-model-invocation`，但不要仅凭 frontmatter 宣称客户端已强制实现手动门控。

使用当前会话原生文件、Shell / SSH 工具及权限；不借适配开启 `/boost`、teamwork 或更宽权限。安装与清单检查不等于已验证真实模型委派。

依据：[agy 子代理](https://antigravity.google/docs/subagents/)、[Skills](https://antigravity.google/docs/skills/)。
