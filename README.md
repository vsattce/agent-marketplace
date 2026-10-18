# agent-marketplace

长期维护的个人 Skill / Plugin Marketplace 项目，客户端显示为 **Agent Marketplace**。支持 Codex、Claude Code 与 Antigravity CLI（agy），多数 Skill 内容与资源共用，并按客户端适配原生工具。

代码托管使用 [Gitee](https://gitee.com/vsattce/agent-marketplace) 和 [GitHub](https://github.com/vsattce/agent-marketplace) 双远端：`origin` 为 Gitee（`git@gitee.com:vsattce/agent-marketplace.git`），`github` 为 GitHub（`git@github.com:vsattce/agent-marketplace.git`）。提交后优先推送 Gitee，再推送 GitHub；GitHub 推送失败不阻塞任务。提交、推送与拉取约定见 [AGENTS.md](AGENTS.md#仓库维护规则)。

三个客户端均包含 **6 个 Plugin**；Codex 有 **21 个 Skills**，Claude Code / agy 各有 **20 个**。四个第三方聚合 Plugin 共 13 项；本仓库自有的 `agent-manager` 在 Codex 有 2 项，Claude Code / agy 各有 1 项，`personal-dev` 三端各有 6 项。

`software-dev` 收录第三方上游项目的 Skills，仅供个人使用与整理；原作者署名、上游内容及许可证均按原样保留。该说明只适用于 `software-dev`；`agent-manager` 和 `personal-dev` 是本仓库自有并直接维护的 Plugin。

## 包含哪些能力

| Plugin | 用途 | Skills |
| --- | --- | --- |
| `common-workflow` | 通用工作流 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `software-dev` | 软件开发 | frontend-design、web-design-guidelines、vue、fastapi、java-springboot |
| `engineering-tools` | 跨技术栈工程工具 | docker-build-strategies、docker-compose-patterns |
| `testing-automation` | 测试与自动化 | playwright-cli |
| `agent-manager` | Agent 管理工具 | am-config；am-context（仅 Codex） |
| `personal-dev` | 个人开发工具，Codex / Claude Code / agy | dev-prepare、dev-delegate、dev-auto、dev-review、dev-simplify、dev-runtime-check |

Codex / Claude Code 按分类安装，完整身份为 `<plugin>@agent-marketplace`。

agy 使用本地产品插件安装，进入本仓库后调用项目 Skill `$sync-agy`（Claude / agy 为 `/sync-agy`），检查或同步当前工作区的全部产品插件到 agy 全局；不导入本仓库开发工具。agy 使用 `/vue`、`/am-config`、`/dev-auto` 等当前会话实际提供的入口。安装、更新及项目作用域限制见[使用手册 · agy](docs/usage.md#antigravity-cliagy)。

## 从哪里开始

| 需要做什么 | 文档入口 |
| --- | --- |
| 已安装，查看调用方式和示例 | [使用手册 · 日常调用](docs/usage.md#日常调用) |
| 查某个 Skill 的用途 | [使用手册 · Skill 速查](docs/usage.md#skill-速查) |
| 编辑项目 Agent 配置或只读查冲突 | [使用手册 · Agent 管理工具](docs/usage.md#agent-管理工具) |
| 换电脑安装，或刷新安装副本 | [使用手册 · 安装与更新](docs/usage.md#安装与更新) |
| 维护来源、同步快照、开发与验证 | [维护指南](docs/maintenance.md) |

## 常用调用

| 操作 | Codex | Claude Code |
| --- | --- | --- |
| 使用 Vue 3 基础 Skill | `$software-dev:vue` | `/software-dev:vue` |
| 使用 FastAPI Skill | `$software-dev:fastapi` | `/software-dev:fastapi` |
| 使用 Docker 构建策略 | `$engineering-tools:docker-build-strategies` | `/engineering-tools:docker-build-strategies` |
| 编排 Docker Compose 服务 | `$engineering-tools:docker-compose-patterns` | `/engineering-tools:docker-compose-patterns` |
| 交接当前任务 | `$common-workflow:handoff` | `/common-workflow:handoff` |
| 估算本轮可见上下文（仅 Codex） | `$agent-manager:am-context` | — |
| 编辑项目配置 / 只读查冲突 | `$agent-manager:am-config` | `/agent-manager:am-config` |
| 准备 SPEC / PLAN，确认后结束 | `$personal-dev:dev-prepare` | `/personal-dev:dev-prepare` |
| 按既定 SPEC / PLAN 执行 SDD | `$personal-dev:dev-delegate` | `/personal-dev:dev-delegate` |
| 自动准备并连续委派开发 | `$personal-dev:dev-auto` | `/personal-dev:dev-auto` |
| 增强代码审查 | `$personal-dev:dev-review` | `/personal-dev:dev-review` |
| 精简当前改动 | `$personal-dev:dev-simplify` | `/personal-dev:dev-simplify` |
| 诊断远端运行问题 | `$personal-dev:dev-runtime-check` | `/personal-dev:dev-runtime-check` |

`handoff`、`agent-manager` 和 `personal-dev` 中的 Skills **仅手动调用**；其余 Skill 可按任务匹配，也可显式调用。启用 Plugin 不会自行执行任务。

`dev-prepare` 结合项目规则和现有代码生成 `spec.md` / `plan.md`，统一确认一次后结束，不开发；`dev-delegate` 只消费已确定的文件执行 SDD，缺失时提示先准备；`dev-auto` 复用同一准备契约和执行器，自动检查后连续开发，正常需求不确认，仅重大歧义、未授权破坏性操作、安全边界不清允许集中询问一次。始终遵循 `SPEC > PLAN > Coder interpretation`。使用与边界见[个人开发工具](docs/usage.md#个人开发工具codex--claude-code)。

SPEC / PLAN 默认保存在 `.agent-tmp/dev-delegate/<task-id>/`，单任务也保存；多任务在同目录加 `progress.md`。Codex 沿用同代 Luna 默认 `high` 编码、`xhigh` 独立验收；Claude 沿用原生子代理配置；用户指定优先，展示后执行，不确认模型 / effort。每任务最多三轮修复加收敛裁决，失败只冻结依赖链及受风险影响的任务，其他任务继续。两端自动识别独立任务，满足安全条件默认两个编码代理并行；有依赖、冲突或并发能力不明时串行，派发时说明理由。主模型始终整体检查；独立 Final Reviewer 仅在用户要求、安全权限、并发事务、破坏性迁移或明显公共 API 不兼容风险时触发，不按改动量或复杂度触发。

`dev-review` 仅在显式调用后审查，默认覆盖当前项目全部自有代码，即使没有 diff；指定范围时严格遵守。它只读源码与配置，先集中预检，再派发审查和必要的独立复核；没有生产证据时仍可完成代码层审查。问题按证据与影响分级，报告保存在项目的 `docs/personal-dev/reviews/<review-id>/report.md`，审查过程不自动提交或推送。使用与边界见[个人开发工具](docs/usage.md#个人开发工具codex--claude-code)。

`dev-runtime-check` 仅在显式调用后通过当前 Harness 的原生 Shell / SSH 工具检查指定的主机、容器或服务；默认只读并在聊天中汇报，用户明确要求修复时仅处理授权范围内的操作。只有用户要求保存结果时才写入 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。报告以目标证据、采样间隔和单位为准，不记录凭据。使用与边界见[使用手册](docs/usage.md#远端运行诊断)。

`dev-simplify` 默认先检查当前工作区差异，只读提出行为等价的精简建议；确认或明确要求执行后才修改。该 Skill 限当前项目与任务，依照目标项目规则和既有授权处理，详见[使用手册](docs/usage.md#精简当前改动)。

`agent-manager` 有两个 Codex 手动入口，Claude Code / agy 各有一个。Codex 的 `am-context` 只估算当前对话已可见内容，不读取外部来源；Codex / Claude 的 `am-config` 处理明确的项目 `AGENTS.md` 编辑、指定来源的 standalone Skill 安装、项目 Plugin 准备/注册及项目开关，也可只读查找冲突。agy 的 `/am-config` 支持项目指令、Skill 安装、Plugin 文件准备及只读检查，项目 Plugin 开关尚未验证。编辑前检查本次操作相关的冲突、重复与加载边界；轻微差异简述，实质冲突详细报告，未明确取舍前停止写入。新 Plugin 不因尚未安装就拒绝合法准备；必要时在项目内隔离验证，分别报告配置已保存与实际加载状态。默认不改日常用户配置、不转向全局安装；单个 Skill 项目开关暂不支持，见[使用手册](docs/usage.md#agent-管理工具)。

Marketplace 第三方来源以 [sources.yaml](sources.yaml) 为准，同步 commit 记录在 [sources.lock.json](sources.lock.json)。本仓库自有脚本与 metadata 使用 [MIT License](LICENSE)，第三方内容遵守各自附带的许可证。

## 本项目使用的 Superpowers Skills

本项目另在 `.agents/skills/` 安装了 [obra/superpowers](https://github.com/obra/superpowers) 的完整 15 个 Skills，供本仓库开发使用，不计入上述 Marketplace Plugin 与 Skill 数量。安装范围仅限当前项目，保留上游 Skill 内容、配套脚本与参考资料。

本仓库维护默认从 `using-superpowers` 开始，按任务类型选择相应流程并保持验证深度与任务风险匹配；手动 Skill 的调用条件、只读及 Git 边界仍按该次调用执行。具体规则见 [AGENTS.md](AGENTS.md#默认工作流程)。

包含 brainstorming、diagnosing-superpowers、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、receiving-code-review、requesting-code-review、subagent-driven-development、systematic-debugging、test-driven-development、using-git-worktrees、using-superpowers、verification-before-completion、writing-plans、writing-skills。

安装快照固定在 `bb92a77741419a4ab5f06e711a283343f1ada0c3`，完整来源与清单见 [.agents/superpowers/source.json](.agents/superpowers/source.json)，上游 MIT 许可证见 [.agents/superpowers/LICENSE](.agents/superpowers/LICENSE)。这些项目 Skills 独立于 `sources.yaml`，不由 Marketplace 同步脚本更新。Codex 安装后可在下一轮对话使用，例如 `$using-superpowers` 或 `$brainstorming`。这些第三方项目 Skills 保持上游内容。

自有 Plugin 与项目 Skill 的双平台维护要求见 [AGENTS.md](AGENTS.md)。项目升级入口在 Codex 为 `$upgrade`、Claude Code 为 `/upgrade`，共用执行正文，见[维护指南](docs/maintenance.md#使用项目-skill)。

本仓库临时目录按任务创建，完成后清理；Windows / PowerShell 的路径核验、普通精确递归删除和失败保留规则见 [AGENTS.md](AGENTS.md#任务产物目录)。自有 Skill 在目标项目使用时，同样遵循随包的 [personal-dev 清理规则](plugins/personal-dev/references/artifacts.md#临时目录清理)与 [am-config 隔离验证规则](plugins/agent-manager/skills/am-config/references/project-edits.md#隔离加载验证)。

本仓库通过 [.codex/config.toml](.codex/config.toml) 为 Codex 配置 Context7 与 OpenAI Docs 官方远程 MCP，按 [AGENTS.md](AGENTS.md) 中的规则按需查阅。该配置只作用于受信任项目的 Codex 会话，不属于 Marketplace Plugin；Claude Code 使用自己的项目 MCP 配置，不套用 Codex 配置。工具用途、查阅边界与加载方式见[维护指南](docs/maintenance.md#仓库开发工具)。配置变更后经 Codex MCP 重载或新会话确认工具可用。

Claude Code plugin 的开发参考固定在项目内的官方 `plugin-dev` 快照，由 Codex 项目 Skill `$claude-plugin-dev` 按需引导；来源、路径与刷新边界见[维护指南](docs/maintenance.md#claude-code-plugin-开发指导)。
