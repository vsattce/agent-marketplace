# agent-marketplace

长期维护的个人 Skill / Plugin Marketplace 项目，客户端显示为 **Agent Marketplace**。目前仅支持 Codex 与 Claude Code，共享同一份 Skill 内容与资源，并按客户端适配原生工具；其他客户端暂不适配或维护。

Codex / Claude Code 均包含 **6 个 Plugin、22 个 Skills**：四个第三方聚合 Plugin（14 项）、本仓库直接维护的 `agent-manager`（3 项）和 `personal-dev`（5 项）。

`software-dev` 收录第三方上游项目的 Skills，仅供个人使用与整理；原作者署名、上游内容及许可证均按原样保留。该说明只适用于 `software-dev`；`agent-manager` 和 `personal-dev` 是本仓库自有并直接维护的 Plugin。

## 包含哪些能力

| Plugin | 用途 | Skills |
| --- | --- | --- |
| `common-workflow` | 通用工作流 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `software-dev` | 软件开发 | frontend-design、web-design-guidelines、vue-best-practices、fastapi、java-spring-boot |
| `engineering-tools` | 跨技术栈工程工具 | docker-build-strategies |
| `testing-automation` | 测试与自动化 | webapp-testing、playwright-cli、playwright-best-practices |
| `agent-manager` | Agent 管理工具 | am-conflict、am-update、am-config |
| `personal-dev` | 个人开发工具，Codex / Claude Code | dev-delegate、dev-review、dev-yagni、dev-simplify、dev-runtime-check |

Codex / Claude Code 按分类安装，完整身份为 `<plugin>@agent-marketplace`。

## 从哪里开始

| 需要做什么 | 文档入口 |
| --- | --- |
| 已安装，查看调用方式和示例 | [使用手册 · 日常调用](docs/usage.md#日常调用) |
| 查某个 Skill 的用途 | [使用手册 · Skill 速查](docs/usage.md#skill-速查) |
| 查冲突、检查更新、配置项目开关 | [使用手册 · Agent 管理工具](docs/usage.md#agent-管理工具) |
| 换电脑安装，或刷新安装副本 | [使用手册 · 安装与更新](docs/usage.md#安装与更新) |
| 维护来源、同步快照、开发与验证 | [维护指南](docs/maintenance.md) |

## 常用调用

| 操作 | Codex | Claude Code |
| --- | --- | --- |
| 使用 Vue 开发规范 | `$software-dev:vue-best-practices` | `/software-dev:vue-best-practices` |
| 使用 FastAPI Skill | `$software-dev:fastapi` | `/software-dev:fastapi` |
| 使用 Docker 构建策略 | `$engineering-tools:docker-build-strategies` | `/engineering-tools:docker-build-strategies` |
| 交接当前任务 | `$common-workflow:handoff` | `/common-workflow:handoff` |
| 只读检查更新 | `$agent-manager:am-update` | `/agent-manager:am-update` |
| 委派开发与独立验收 | `$personal-dev:dev-delegate` | `/personal-dev:dev-delegate` |
| 增强代码审查 | `$personal-dev:dev-review` | `/personal-dev:dev-review` |
| 按需实现 | `$personal-dev:dev-yagni` | `/personal-dev:dev-yagni` |
| 精简当前改动 | `$personal-dev:dev-simplify` | `/personal-dev:dev-simplify` |
| 诊断远端运行问题 | `$personal-dev:dev-runtime-check` | `/personal-dev:dev-runtime-check` |

`handoff`、三个 Agent 管理 Skill 和 `personal-dev` 中的 Skills **仅手动调用**；其余 Skill 可按任务匹配，也可显式调用。启用 Plugin 不会自行执行任务。

`dev-delegate` 由当前主模型安排任务、最终整体检查；Codex 自动选择同大版本最新可用 Luna，默认 `xhigh` 编码，另一个同型号代理以 `max`（最强）验收；用户可分别指定强度，未指定的角色使用默认值。Claude Code 沿用当前子代理模型与思考配置，用户指定时按原生工具能力核验。开始前显示模型策略与已确认的实际值，再直接执行；判断不明确或两轮修复仍阻塞时中断，由用户决定。改名系列须明确确认，不自动猜测或跨代降级。使用与边界见[个人开发工具](docs/usage.md#个人开发工具codex--claude-code)。

`dev-review` 仅在显式调用后审查，默认覆盖当前项目全部自有代码，即使没有 diff；指定范围时严格遵守。它只读源码与配置，先集中预检，再派发审查和必要的独立复核；没有生产证据时仍可完成代码层审查。问题按证据与影响分级，报告保存在项目的 `docs/reviews/`。使用与边界见[个人开发工具](docs/usage.md#个人开发工具codex--claude-code)。

`dev-runtime-check` 仅在显式调用后通过当前 Harness 的原生 Shell / SSH 工具检查指定的主机、容器或服务；默认只读，用户明确要求修复时仅处理授权范围内的操作。报告以目标证据、采样间隔和单位为准，不记录凭据。使用与边界见[使用手册](docs/usage.md#远端运行诊断)。

`dev-yagni` 明确调用且目标清楚、没有只读或暂缓要求时默认由当前模型实现最小完整结果；只要求方案时等待确认。`dev-simplify` 默认先检查当前工作区差异，只读提出行为等价的精简建议；确认或明确要求执行后才修改。两者限当前项目与任务，依照目标项目规则和既有授权处理，详见[使用手册](docs/usage.md#按需实现与精简)。

`am-config` 仅手动处理明确的项目 `AGENTS.md` 编辑、指定来源的 standalone Skill 安装和已支持的 Codex / Claude Plugin 开关；Plugin 项目安装及单个 Skill 开关暂不支持，其他 Harness 会拒绝。所有操作先检查冲突、重复和 Harness 加载边界，见[使用手册](docs/usage.md#项目开关支持范围)。

Marketplace 第三方来源以 [sources.yaml](sources.yaml) 为准，同步 commit 记录在 [sources.lock.json](sources.lock.json)。本仓库自有脚本与 metadata 使用 [MIT License](LICENSE)，第三方内容遵守各自附带的许可证。

## 本项目使用的 Superpowers Skills

本项目另在 `.agents/skills/` 安装了 [obra/superpowers](https://github.com/obra/superpowers) 的完整 15 个 Skills，供本仓库开发使用，不计入上述 Marketplace Plugin 与 Skill 数量。安装范围仅限当前项目，保留上游 Skill 内容、配套脚本与参考资料。

包含 brainstorming、diagnosing-superpowers、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、receiving-code-review、requesting-code-review、subagent-driven-development、systematic-debugging、test-driven-development、using-git-worktrees、using-superpowers、verification-before-completion、writing-plans、writing-skills。

安装快照固定在 `bb92a77741419a4ab5f06e711a283343f1ada0c3`，完整来源与清单见 [.agents/superpowers/source.json](.agents/superpowers/source.json)，上游 MIT 许可证见 [.agents/superpowers/LICENSE](.agents/superpowers/LICENSE)。这些项目 Skills 独立于 `sources.yaml`，不由 Marketplace 同步脚本更新。Codex 安装后可在下一轮对话使用，例如 `$using-superpowers` 或 `$brainstorming`。这些第三方项目 Skills 保持上游内容。

自有 Plugin 与项目 Skill 的双平台维护要求见 [AGENTS.md](AGENTS.md)。项目升级入口在 Codex 为 `$upgrade`、Claude Code 为 `/upgrade`，共用执行正文，见[维护指南](docs/maintenance.md#使用项目-skill)。

本仓库通过 [.codex/config.toml](.codex/config.toml) 为 Codex 配置 Context7 与 OpenAI Docs 官方远程 MCP，按 [AGENTS.md](AGENTS.md) 中的规则按需查阅。该配置只作用于受信任项目的 Codex 会话，不属于 Marketplace Plugin；Claude Code 使用自己的项目 MCP 配置，不套用 Codex 配置。工具用途、查阅边界与加载方式见[维护指南](docs/maintenance.md#仓库开发工具)。配置变更后经 Codex MCP 重载或新会话确认工具可用。

Claude Code plugin 的开发参考固定在项目内的官方 `plugin-dev` 快照，由 Codex 项目 Skill `$claude-plugin-dev` 按需引导；来源、路径与刷新边界见[维护指南](docs/maintenance.md#claude-code-plugin-开发指导)。
