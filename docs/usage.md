# 使用手册

[返回首页](../README.md) · [维护指南](maintenance.md)

已经安装并启用 Marketplace 的用户，从日常调用开始；安装步骤用于首次安装、换电脑或更新副本。

## 日常调用

在聊天中写明 Skill 和要完成的任务：

| 客户端 | 调用格式 | 示例 |
| --- | --- | --- |
| Codex | `$<plugin>:<skill>` | `$frontend-dev:vue 帮我实现这个组件` |
| Claude Code | `/<plugin>:<skill>` | `/frontend-dev:vue 帮我实现这个组件` |
| Kimi Code | `/skill:<name>` | `/skill:vue 帮我实现这个组件` |

Kimi 的 Skill 名称不带分类前缀。可用入口以当前会话实际显示的清单为准。

**仅手动调用**：`handoff`、`resolve-conflicts`、`check-updates`、`configure-project`。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

例如在 Codex 中：

```text
$common-workflow:handoff 整理当前进度，供新会话继续
$agent-manager:resolve-conflicts 检查当前项目与全局规则的冲突
$agent-manager:check-updates 检查已记录来源和安装副本是否有更新
```

## Skill 速查

| Plugin | Skill | 用途 | 调用方式 |
| --- | --- | --- | --- |
| common-workflow | handoff | 整理进度、决定和后续工作，供新会话接续 | 仅手动 |
| common-workflow | diagnosing-bugs | 排查复杂 Bug、报错、故障和性能回归 | 任务匹配 / 手动 |
| common-workflow | research | 从可信来源收集资料和 API 文档，形成研究记录 | 任务匹配 / 手动 |
| common-workflow | writing-for-agents | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 | 任务匹配 / 手动 |
| common-workflow | find-skills | 按需求查找 Skill，了解能力与安装方式 | 任务匹配 / 手动 |
| frontend-dev | frontend-design | 指导新页面或改版的视觉风格、排版和细节 | 任务匹配 / 手动 |
| frontend-dev | web-design-guidelines | 审查 Web 界面、可访问性和交互规范 | 任务匹配 / 手动 |
| frontend-dev | vue | 指导 Vue 3 组件、Composition API 与响应式逻辑 | 任务匹配 / 手动 |
| frontend-dev | vue-best-practices | 指导 Vue、Vue Router、Pinia 和 Vite 开发实践 | 任务匹配 / 手动 |
| backend-dev | java-spring-boot | 指导 REST API、安全认证、数据访问与 Actuator | 任务匹配 / 手动 |
| testing-automation | webapp-testing | 验证本地网页交互，查看截图与控制台日志 | 任务匹配 / 手动 |
| testing-automation | playwright-cli | 通过 Playwright CLI 操作浏览器并验证交互 | 任务匹配 / 手动 |
| testing-automation | playwright-best-practices | 指导 Playwright 测试、模拟、认证、调试与 CI | 任务匹配 / 手动 |
| agent-manager | resolve-conflicts | 只读查找项目与全局指令、Skill、Plugin 的冲突和歧义 | 仅手动 |
| agent-manager | check-updates | 只读比较既定来源、仓库、安装副本与 Marketplace 状态 | 仅手动 |
| agent-manager | configure-project | 执行用户明确指定的当前项目 Plugin 开关 | 仅手动 |

## Agent 管理工具

### 查找冲突

`resolve-conflicts` 按当前 Agent 的实际加载规则检查项目与全局来源，在对话中报告双方原文、位置、触发条件、影响及最小建议。它区分冲突、歧义、能力重叠和已有覆盖规则消解的差异。

全过程只读，不改配置、不禁用或卸载入口，也不创建报告文件。来源或加载状态不明时标记 `UNKNOWN`，扫描不完整时标记 `PARTIAL`。

### 检查更新

`check-updates` 支持 Codex、Claude Code 与 Kimi Code，只比较已记录的 repo / path / ref、精确 commit 和安装证据，不更新对象或更换来源。固定 commit 不跟随 main；版本字符串相同也不代表内容相同。

源码快照、Marketplace 快照和客户端安装副本分别报告。来源无法确认时标记 `UNKNOWN SOURCE`，证据不足时标记 `UNKNOWN` 或 `BLOCKED`。

需要实际更新时，维护仓库按[维护指南](maintenance.md#升级第三方-skill)同步，再按下方对应客户端步骤刷新安装副本。

### 配置项目开关

调用时逐项指定完整 Plugin 身份及启用 / 禁用状态，例如：

```text
$agent-manager:configure-project 在当前项目禁用 frontend-dev@agent-marketplace，启用 testing-automation@agent-marketplace
```

Claude 使用 `/agent-manager:configure-project`。它只修改 Git 确认的当前项目根配置，不推荐组合、不安装缺失目标、不更新 Plugin，也不提交或推送用户项目。

#### 项目开关支持范围

以下版本范围仅针对 `configure-project` 的配置执行能力：

| 客户端与已验证版本 | 项目 Plugin 开关 | 写入位置 |
| --- | --- | --- |
| Codex `0.162.0-alpha.2` | 已安装的本地 Marketplace Plugin | `.codex/config.toml` |
| Claude Code `2.1.296` | 已安装的 Marketplace Plugin | `.claude/settings.json` |
| Kimi Code Desktop `1.0.4` | 暂不支持，整批 `BLOCKED` | 不写配置 |

三个客户端的**单个 Skill 项目开关均不支持**。未验证的 Codex / Claude 版本、目标缺失或歧义、配置损坏、有效项目层证据不足，以及 Codex 未受信任项目或 workspace-managed Plugin，均拒绝整批操作。Claude 的 `.claude/settings.local.json` 若对目标存在反向覆盖，也会整批拒绝。

任何一个目标不受支持，整个批次都不写入。全局与项目外配置始终只读；保存后重新加载项目或新建会话，才确认新的会话状态。详细能力证据见 [Codex](../plugins/agent-manager/skills/configure-project/references/codex-support.md)、[Claude](../plugins/agent-manager/skills/configure-project/references/claude-support.md) 与 [Kimi](../plugins/agent-manager/references/kimi.md)。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Codex

从 GitHub 添加 Marketplace，再安装需要的分类；下面列出全部五类，可按需选择：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add frontend-dev@agent-marketplace --json
codex plugin add backend-dev@agent-marketplace --json
codex plugin add testing-automation@agent-marketplace --json
codex plugin add agent-manager@agent-marketplace --json
```

安装后默认启用，可在 UI 中单独启用或禁用整个分类。新建聊天加载入口；界面未刷新时重开客户端。

本地开发可用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。用 `codex plugin marketplace list` 核对注册，`codex plugin list --marketplace agent-marketplace --available --json` 查看可安装入口；切换同名市场来源前先核对旧注册。

**刷新**：本地来源同步后，重新执行对应的 `codex plugin add <plugin>@agent-marketplace --json`。GitHub 来源先刷新客户端中的 Marketplace 快照，再重新安装对应 Plugin，最后新建聊天。

### Claude Code

从 GitHub 添加并按需安装分类：

```powershell
claude plugin marketplace add vsattce/agent-marketplace
claude plugin install common-workflow@agent-marketplace
claude plugin install frontend-dev@agent-marketplace
claude plugin install backend-dev@agent-marketplace
claude plugin install testing-automation@agent-marketplace
claude plugin install agent-manager@agent-marketplace
```

安装默认 user scope；仅某个项目需要时，使用 `claude plugin install <plugin>@agent-marketplace --scope project`。可用 `claude plugin list --json` 或 `claude plugin details <plugin>` 查看安装信息。

本地开发使用 `claude plugin marketplace add E:\WorkSpace\agent-marketplace`。当前已验证版本的本地目录来源直接加载源目录，编辑后新建会话或执行 `/reload-plugins`。

**刷新 GitHub 来源**：先更新市场，再更新需要的 Plugin，例如：

```powershell
claude plugin marketplace update agent-marketplace
claude plugin update frontend-dev@agent-marketplace
```

其他分类同理，完成后新建会话。切换同名市场来源前先核对注册；移除 Marketplace 会同时卸载其插件。

### Kimi Code

桌面客户端进入「设置 → 插件 → 安装自定义插件」，粘贴以下地址可一次安装全部 16 个 Skills：

```text
https://github.com/vsattce/agent-marketplace/tree/main
```

也支持 `https://github.com/vsattce/agent-marketplace.git`；显式指定 main 可避免未来 release 改变默认 URL 的版本选择。CLI 的 `/plugins install <地址或绝对路径>` 是 Kimi 聊天命令，不是 PowerShell 命令；此入口不支持 `git@github.com:...` SSH 地址。

本地安装可填 `E:\WorkSpace\agent-marketplace`；只需某分类时，填对应绝对目录，例如 `E:\WorkSpace\agent-marketplace\plugins\frontend-dev`。本机已验证的 1.0.4 不支持用 GitHub `/tree/main/plugins/<分类>` URL 安装子目录。整仓库聚合安装与分类安装二选一，避免重复提供 Skills。

**刷新**：重新安装，保持插件启用，再新建会话；CLI 可用 `/reload` 或 `/new`。本地来源也会复制到托管目录，修改原目录后仅重载不会复制新内容。Kimi 的插件开关是用户级，影响所有项目。

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 仓库已更新，客户端仍是旧内容 | 按对应客户端刷新安装副本，再新建会话 |
| 已安装，但当前聊天找不到入口 | 核对启用状态和当前会话清单，重新加载或新建聊天；磁盘存在不等于会话可用 |
| 不知道 Skill 是否自动执行 | handoff 和三个管理入口仅手动；其他入口按任务匹配，启用不会自行执行 |
| 配置开关返回 BLOCKED | 查看具体原因及上方支持范围；安装成功不代表具备所有项目配置能力 |
| Kimi 出现重复 Skill | 检查是否同时安装整仓库聚合插件和分类插件 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[Kimi Plugins](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/plugins.md)、[Kimi Skills](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/skills.md)。
