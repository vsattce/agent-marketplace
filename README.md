# agent-marketplace

个人使用的 Skill / Plugin 集合，客户端显示为 **Agent Marketplace**。五个分类支持 Codex、Claude Code 与 Kimi Code，共享同一份 Skill 内容与资源；`personal-dev` 仅支持 Codex，Antigravity 尚未适配。

目前 Codex 包含 **6 个 Plugin、18 个 Skills**：四个第三方聚合 Plugin（13 项）、本仓库直接维护的 `agent-manager`（3 项）和 `personal-dev`（2 项）。Claude / Kimi 保持五个 Plugin、16 个 Skills。

## 包含哪些能力

| Plugin | 用途 | Skills |
| --- | --- | --- |
| `common-workflow` | 通用工作流 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `frontend-dev` | 前端开发 | frontend-design、web-design-guidelines、vue、vue-best-practices |
| `backend-dev` | 后端开发 | java-spring-boot |
| `testing-automation` | 测试与自动化 | webapp-testing、playwright-cli、playwright-best-practices |
| `agent-manager` | Agent 管理工具 | resolve-conflicts、check-updates、configure-project |
| `personal-dev` | 个人开发工具，仅 Codex | delegated-development、review |

Codex / Claude 按分类安装，完整身份为 `<plugin>@agent-marketplace`；Kimi 可一次安装整个仓库，也可按本地分类目录安装。

## 从哪里开始

| 需要做什么 | 文档入口 |
| --- | --- |
| 已安装，查看调用方式和示例 | [使用手册 · 日常调用](docs/usage.md#日常调用) |
| 查某个 Skill 的用途 | [使用手册 · Skill 速查](docs/usage.md#skill-速查) |
| 查冲突、检查更新、配置项目开关 | [使用手册 · Agent 管理工具](docs/usage.md#agent-管理工具) |
| 换电脑安装，或刷新安装副本 | [使用手册 · 安装与更新](docs/usage.md#安装与更新) |
| 维护来源、同步快照、开发与验证 | [维护指南](docs/maintenance.md) |

## 常用调用

| 操作 | Codex | Claude Code | Kimi Code |
| --- | --- | --- | --- |
| 使用 Vue Skill | `$frontend-dev:vue` | `/frontend-dev:vue` | `/skill:vue` |
| 交接当前任务 | `$common-workflow:handoff` | `/common-workflow:handoff` | `/skill:handoff` |
| 只读检查更新 | `$agent-manager:check-updates` | `/agent-manager:check-updates` | `/skill:check-updates` |
| 委派开发与独立验收 | `$personal-dev:delegated-development` | 暂不支持 | 暂不支持 |
| 增强代码审查 | `$personal-dev:review` | 暂不支持 | 暂不支持 |

`handoff`、三个 Agent 管理 Skill 和 `personal-dev` 中的 Skills **仅手动调用**；其余 Skill 可按任务匹配，也可显式调用。启用 Plugin 不会自行执行任务。

`delegated-development` 由当前主模型安排任务、最终整体检查；自动选择同大版本最新可用 Luna，默认 `xhigh` 编码，另一个同型号代理以 `max` 验收。开始前显示实际模型与强度，再直接执行；判断不明确或两轮修复仍阻塞时中断，由用户决定。改名系列须明确确认，不自动猜测或跨代降级。使用与边界见[个人开发工具](docs/usage.md#个人开发工具仅-codex)。

`review` 仅在显式调用后审查，默认覆盖当前项目全部自有代码，即使没有 diff；指定范围时严格遵守。它只读源码与配置，先集中预检，再派发审查和必要的独立复核；没有生产证据时仍可完成代码层审查。问题按证据与影响分级，报告保存在项目的 `docs/reviews/`。使用与边界见[个人开发工具](docs/usage.md#个人开发工具仅-codex)。

`configure-project` 当前支持已验证版本的 Codex / Claude 项目 Plugin 开关；单个 Skill 开关和 Kimi 项目开关暂不支持。具体范围见[使用手册](docs/usage.md#项目开关支持范围)。

Marketplace 第三方来源以 [sources.yaml](sources.yaml) 为准，同步 commit 记录在 [sources.lock.json](sources.lock.json)。本仓库自有脚本与 metadata 使用 [MIT License](LICENSE)，第三方内容遵守各自附带的许可证。

## 本项目使用的 Superpowers Skills

本项目另在 `.agents/skills/` 安装了 [obra/superpowers](https://github.com/obra/superpowers) 的完整 15 个 Skills，供本仓库开发使用，不计入上述 Marketplace Plugin 与 Skill 数量。安装范围仅限当前项目，保留上游 Skill 内容、配套脚本与参考资料。

包含 brainstorming、diagnosing-superpowers、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、receiving-code-review、requesting-code-review、subagent-driven-development、systematic-debugging、test-driven-development、using-git-worktrees、using-superpowers、verification-before-completion、writing-plans、writing-skills。

安装快照固定在 `bb92a77741419a4ab5f06e711a283343f1ada0c3`，完整来源与清单见 [.agents/superpowers/source.json](.agents/superpowers/source.json)，上游 MIT 许可证见 [.agents/superpowers/LICENSE](.agents/superpowers/LICENSE)。这些项目 Skills 独立于 `sources.yaml`，不由 Marketplace 同步脚本更新。安装后可在下一轮对话使用，例如 `$using-superpowers` 或 `$brainstorming`。
