# agent-marketplace

长期维护的个人 Skill / Plugin Marketplace 项目，客户端显示为 **Agent Marketplace**。支持 Codex、Claude Code、Antigravity CLI（agy）与 DeepSeek Harness 桌面版（dsh），多数 Skill 内容与资源共用，并按客户端适配原生工具。

代码托管使用 [Gitee](https://gitee.com/vsattce/agent-marketplace) 和 [GitHub](https://github.com/vsattce/agent-marketplace) 双远端：`origin` 为 Gitee（`git@gitee.com:vsattce/agent-marketplace.git`），`github` 为 GitHub（`git@github.com:vsattce/agent-marketplace.git`）。提交后优先推送 Gitee，再推送 GitHub；GitHub 推送失败不阻塞任务。提交、推送与拉取约定见 [AGENTS.md](AGENTS.md#仓库维护规则)。

产品目录包含 **4 个 Plugin**、**26 个 Skills**，四端使用同一产品清单：matt 17、common-workflow 1、software-dev 5、engineering-tools 3。这是仓库入口数量，不代表当前会话已加载。

`software-dev` 收录第三方上游项目的 Skills，仅供个人使用与整理；原作者署名、上游内容及许可证均按原样保留。

## 包含哪些能力

| Plugin | 用途 | Skills |
| --- | --- | --- |
| `common-workflow` | 非 Matt 通用能力 | find-skills |
| `matt` | Matt 精选工作流，完整目录与运行依赖 | setup-matt-pocock-skills、grill-with-docs、grilling、domain-modeling、to-spec、to-tickets、implement、implement-spec、tdd、codebase-design、code-review、handoff、diagnosing-bugs、research、improve-codebase-architecture、writing-for-agents、retro |
| `software-dev` | 软件开发 | frontend-design、web-design-guidelines、vue、fastapi、java-springboot |
| `engineering-tools` | 跨技术栈工程工具 | docker-build-strategies、docker-compose-patterns、playwright-cli |

Codex / Claude Code 按分类安装，完整身份为 `<plugin>@agent-marketplace`。

agy 使用本地产品插件安装，进入本仓库后调用项目 Skill `$sync-agy`（Claude / agy 为 `/sync-agy`），检查或同步当前工作区的全部产品插件到 agy 全局；不导入本仓库开发工具。agy 使用 `/vue`、`/implement` 等当前会话实际提供的入口。安装、更新及项目作用域限制见[使用手册 · agy](docs/usage.md#antigravity-cliagy)。

dsh 桌面版使用项目 Skill `$sync-dsh`（Claude / agy 为 `/sync-dsh`），同步当前产品 Skills 与完整资源，通过已安装桌面版自带的加载器验证；调用方式为 `/vue`、`/implement` 等。不按版本号拦截，不需要 npm CLI。见[使用手册 · dsh 桌面版](docs/usage.md#deepseek-harness-桌面版dsh)。

## 从哪里开始

本仓库的工程 Skills 使用[本地 Markdown Issue](docs/agents/issue-tracker.md) 和[单上下文领域文档](docs/agents/domain.md)；配置入口见 [AGENTS.md](AGENTS.md#agent-skills)。

| 需要做什么 | 文档入口 |
| --- | --- |
| 已安装，查看调用方式和示例 | [使用手册 · 日常调用](docs/usage.md#日常调用) |
| 查某个 Skill 的用途 | [使用手册 · Skill 速查](docs/usage.md#skill-速查) |
| 换电脑安装，或刷新安装副本 | [使用手册 · 安装与更新](docs/usage.md#安装与更新) |
| 维护来源、同步快照、开发与验证 | [维护指南](docs/maintenance.md) |

## 常用调用

| 操作 | Codex | Claude Code |
| --- | --- | --- |
| 初始化 Matt Pocock 工程 Skills 的项目配置 | `$matt:setup-matt-pocock-skills` | `/matt:setup-matt-pocock-skills` |
| 使用 Vue 3 基础 Skill | `$software-dev:vue` | `/software-dev:vue` |
| 使用 FastAPI Skill | `$software-dev:fastapi` | `/software-dev:fastapi` |
| 使用 Docker 构建策略 | `$engineering-tools:docker-build-strategies` | `/engineering-tools:docker-build-strategies` |
| 编排 Docker Compose 服务 | `$engineering-tools:docker-compose-patterns` | `/engineering-tools:docker-compose-patterns` |
| 操作浏览器与验证网页交互 | `$engineering-tools:playwright-cli` | `/engineering-tools:playwright-cli` |
| 交接当前任务 | `$matt:handoff` | `/matt:handoff` |
| 设计模块接口与测试边界 | `$matt:codebase-design` | `/matt:codebase-design` |
| 推敲方案并记录词汇与决策 | `$matt:grill-with-docs` | `/matt:grill-with-docs` |
| 寻找并推敲架构改进机会 | `$matt:improve-codebase-architecture` | `/matt:improve-codebase-architecture` |
| 按测试先行开发 | `$matt:tdd` | `/matt:tdd` |
| 整理需求为 Spec | `$matt:to-spec` | `/matt:to-spec` |
| 大型需求拆分 Ticket | `$matt:to-tickets` | `/matt:to-tickets` |
| 普通开发（默认） | `$matt:implement` | `/matt:implement` |
| 大型多 Ticket 并行开发 | `$matt:implement-spec` | `/matt:implement-spec` |
| 困难 Bug | `$matt:diagnosing-bugs` | `/matt:diagnosing-bugs` |
| Matt 代码审查 | `$matt:code-review` | `/matt:code-review` |
| 手动复盘 Agent 环境 | `$matt:retro` | `/matt:retro` |

Matt 推荐主链为 `grill-with-docs → to-spec → 按需 to-tickets → implement`。普通任务使用 `implement`；仅大型、多 Ticket 且确实适合多 Agent 并行时使用 `implement-spec`。`handoff`、`diagnosing-bugs`、`research`、`improve-codebase-architecture` 独立使用；`retro` 只手动复盘，不加入默认完成流程。

`matt` 只收录 sources 中明确选择的 17 个完整目录，正文、触发策略、agents、模板及引用资源保持 upstream 原样，不添加自定义 wrapper、模型路由或 Harness adapter。`setup-matt-pocock-skills` 配置 issue tracker 与领域文档；运行依赖随包提供，详见[Matt 工作流](docs/usage.md#matt-精选工作流)。

Marketplace 第三方来源以 [sources.yaml](sources.yaml) 为准，同步 commit 记录在 [sources.lock.json](sources.lock.json)。本仓库自有脚本与 metadata 使用 [MIT License](LICENSE)，第三方内容遵守各自附带的许可证。

## 本项目使用的 Superpowers Skills

本项目另在 `.agents/skills/` 安装了 [obra/superpowers](https://github.com/obra/superpowers) 的完整 15 个 Skills，供本仓库开发使用，不计入上述 Marketplace Plugin 与 Skill 数量。安装范围仅限当前项目，保留上游 Skill 内容、配套脚本与参考资料。

Superpowers 及其 Skills 默认不自动调用，只有用户明确手动指定时才使用；指定后仍按任务规模和风险选择必要步骤。普通文档整理、常规 Git 操作和边界明确的小改动直接按项目规则完成。具体规则见 [AGENTS.md](AGENTS.md#默认工作流程)。

包含 brainstorming、diagnosing-superpowers、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、receiving-code-review、requesting-code-review、subagent-driven-development、systematic-debugging、test-driven-development、using-git-worktrees、using-superpowers、verification-before-completion、writing-plans、writing-skills。

安装快照固定在 `bb92a77741419a4ab5f06e711a283343f1ada0c3`，完整来源与清单见 [.agents/superpowers/source.json](.agents/superpowers/source.json)，上游 MIT 许可证见 [.agents/superpowers/LICENSE](.agents/superpowers/LICENSE)。这些项目 Skills 独立于 `sources.yaml`，不由 Marketplace 同步脚本更新。Codex 安装后可在下一轮对话使用，例如 `$using-superpowers` 或 `$brainstorming`。这些第三方项目 Skills 保持上游内容。

自有 Plugin 与项目 Skill 的客户端适配要求见 [AGENTS.md](AGENTS.md)。项目升级入口在 Codex 为 `$upgrade`、Claude Code 为 `/upgrade`，共用执行正文，见[维护指南](docs/maintenance.md#使用项目-skill)。

本仓库临时目录按任务创建，完成后清理；Windows / PowerShell 的路径核验、普通精确递归删除和失败保留规则见 [AGENTS.md](AGENTS.md#任务产物目录)。

自有入口执行命令时跟踪后台 ID 至实际退出，先关闭本次测试 / 客户端进程再清理目录；详见[命令与资源契约](docs/agents/execution-resources.md)。

本仓库通过 [.codex/config.toml](.codex/config.toml) 为 Codex 配置 Context7 与 OpenAI Docs 官方远程 MCP，按 [AGENTS.md](AGENTS.md) 中的规则按需查阅。该配置只作用于受信任项目的 Codex 会话，不属于 Marketplace Plugin；Claude Code 使用自己的项目 MCP 配置，不套用 Codex 配置。工具用途、查阅边界与加载方式见[维护指南](docs/maintenance.md#仓库开发工具)。配置变更后经 Codex MCP 重载或新会话确认工具可用。

Claude Code plugin 的开发参考固定在项目内的官方 `plugin-dev` 快照，由 Codex 项目 Skill `$claude-plugin-dev` 按需引导；来源、路径与刷新边界见[维护指南](docs/maintenance.md#claude-code-plugin-开发指导)。
