# Antigravity CLI（agy）委派适配

仅用于确认当前 Harness 为 Antigravity CLI 的会话，不能从 Gemini 模型名推断客户端。共享需求、角色、修复轮次及终审条件保持不变，不执行 Codex 的 Python 选型器。

## 原生模型与委派

1. 以本轮实际工具 schema 为准，确认 `invoke_subagent`、独立上下文及完成结果读取能力。优先使用具备所需工具的原生 `self` 或当前已发现的通用子代理；`research` 等只读角色不能编码。缺少必要能力时报告具体 `BLOCKED`，不嵌套启动 `agy -p` 或其他客户端补能力。
2. 编码、验收、审查及复核默认继承当前原生子代理的模型与思考配置，不强制 Luna、Flash / Pro、Codex effort 或 Claude 参数。派发前展示各角色的“agy 原生默认 / 继承当前配置”；实际值未公开时标 `UNKNOWN`，不将默认策略冒充已核验型号。用户指定覆写时，仅按本轮支持的参数与可用值执行，不支持则说明限制。
3. 新任务和独立验收使用不同的干净子代理，只传任务、项目、SPEC / PLAN 路径、必要规则与证据。使用当前工作区的共享或继承模式，具体字段按 schema；不为普通任务自动创建分支或 worktree。按共享编排自动判断独立任务，原生并发能力与范围安全均已确认时默认两个编码代理并行，先启动本批再等待；依赖、冲突、能力不明或明确串行要求下使用单写。
4. 验收 / 审查提示明确只读，不修复、不提交、不派生代理。记录原生返回的 agent / conversation ID，按当前状态、结果和消息工具等待或继续；返工优先恢复原编码代理，第三轮按共享契约新建。恢复和重建不清零修复预算，不向其他用户聊天发消息。
5. 独立 Final Reviewer 仍只在主 Skill 的规定条件触发。型号、强度顺序与原生覆写均可核验时采用会话同型号低一档；否则沿用任务验收默认配置并如实显示。用户明确配置优先；一次升级、三轮修复和主模型整体检查的边界保持不变，不为选型修改用户配置。

## 调用与权限

agy 将 Skills 提供为 `/<skill-name>`，例如 `/dev-prepare`、`/dev-delegate`、`/dev-auto`、`/dev-review`、`/dev-simplify`、`/dev-runtime-check`。以当前会话实际展示的命令为准；这些入口仍仅在用户明确调用时执行，普通任务或提及名称不触发。保留 `disable-model-invocation`，但不要仅凭 frontmatter 宣称客户端已强制实现手动门控。

使用当前会话原生文件、Shell / SSH 工具及权限；不借适配开启 `/boost`、teamwork 或更宽权限。安装与清单检查不等于已验证真实模型委派。

依据：[agy 子代理](https://antigravity.google/docs/subagents/)、[Skills](https://antigravity.google/docs/skills/)。
