# agent-marketplace

个人使用的 Skill / Plugin 集合，客户端显示为 **Agent Marketplace**。支持 Codex、Claude Code 与 Kimi Code，共享同一份 Skill 内容与资源；Antigravity 尚未适配。

目前包含 **5 个分类 Plugin、16 个 Skills**：四个第三方聚合 Plugin（13 项）和本仓库直接维护的 `agent-manager`（3 项）。

## 包含哪些能力

| Plugin | 用途 | Skills |
| --- | --- | --- |
| `common-workflow` | 通用工作流 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `frontend-dev` | 前端开发 | frontend-design、web-design-guidelines、vue、vue-best-practices |
| `backend-dev` | 后端开发 | java-spring-boot |
| `testing-automation` | 测试与自动化 | webapp-testing、playwright-cli、playwright-best-practices |
| `agent-manager` | Agent 管理工具 | resolve-conflicts、check-updates、configure-project |

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

`handoff` 和三个 Agent 管理 Skill **仅手动调用**；其余 Skill 可按任务匹配，也可显式调用。启用 Plugin 不会自行执行任务。

`configure-project` 当前支持已验证版本的 Codex / Claude 项目 Plugin 开关；单个 Skill 开关和 Kimi 项目开关暂不支持。具体范围见[使用手册](docs/usage.md#项目开关支持范围)。

第三方来源以 [sources.yaml](sources.yaml) 为准，同步 commit 记录在 [sources.lock.json](sources.lock.json)。本仓库自有脚本与 metadata 使用 [MIT License](LICENSE)，第三方内容遵守各自附带的许可证。
