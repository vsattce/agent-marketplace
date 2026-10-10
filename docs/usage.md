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

**仅手动调用**：`handoff`、`resolve-conflicts`、`check-updates`、`configure-project`，以及 `personal-dev` 中的 Skills。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

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
| agent-manager | configure-project | 预检后编辑项目指令、安装指定 Skill 或执行受支持的 Plugin 开关 | 仅手动 |
| personal-dev | delegated-development | 主模型安排任务，独立编码与验收代理执行，主模型最终整体检查；Codex / Claude Code | 仅手动 |
| personal-dev | review | 只读审查当前项目或明确范围，独立复核高等级发现并生成报告；Codex / Claude Code | 仅手动 |

## 个人开发工具（Codex / Claude Code）

```text
$personal-dev:delegated-development 实现当前需求，保留现有接口和范围外行为
$personal-dev:review 检查当前项目的性能、资源、请求、磁盘和长期运行风险
```

Claude Code 使用 `/personal-dev:delegated-development` 与 `/personal-dev:review`，沿用当前子代理模型与思考配置；不覆写 `model` / `effort`，也不要求 Codex 的 Luna、`reasoning_effort` 或 Python 检查器。派发前显示默认策略；实际 ID 或强度无法确认时标 `UNKNOWN`，不冒充已验证值。独立验收、两轮修复上限与主模型终审流程和 Codex 相同。

主模型按可独立验证的功能或修复点拆任务，同类小改动合并。Codex 当前已确认的低成本编码系列为 Luna：从本轮派发工具实际允许的型号中选择与主模型同一大版本内数字版本最高者，默认 `xhigh` 编码；另一个干净上下文的同型号代理默认 `max` 验收。最终由当前主模型检查累计改动与跨任务联动。

Codex 需要本轮可靠的主模型身份、当前派发工具允许名单和支持强度信息。6.1 / 6.2 主模型可以用 6 Luna；7 主模型不能自动回退到 6 或 5.6。信息缺失、陌生命名、版本歧义、强度不支持或工具不能覆写时输出具体原因并中断。用户明确确认精确替代型号后可用于当前任务；持久接纳新系列需另行维护，不凭升级推荐或价格猜测选模型。

编码开始前一定先显示实际结果，例如：

```text
编码模型：gpt-6-luna｜思考强度：xhigh
验收模型：gpt-6-luna｜思考强度：max
```

成功后直接执行，不额外确认是否开始。用户可明确覆写型号或强度；有变化先重新显示。独立验收检查需求、实现、相关调用点和验证证据，阻塞问题完整汇总，风格建议不扩大返工。初次实现后每个任务累计最多两轮修复，第二轮复验仍阻塞则全流程停止，由用户决定升级；主模型不自动接手编码。终审修复沿用相应任务剩余次数。

Codex 随 Skill 提供的 Python 标准库检查器只校验主模型根据当前工具整理的模型信息，不连接服务、不验证输入来源、不修改配置，也不是原生派发工具的强制拦截器。使用已有且符合规则的 Agent 工具解释器；缺少环境时中断，不自动安装或切换。费用与 Codex 额度的实际节省需要实测，不按 API 标价推算固定比例。

Codex / Claude 均注册此 Plugin，Kimi 暂不注册。安装后新建对应客户端会话加载；仓库有文件或已经推送，不代表当前会话已注入新 Skill。该 Skill 执行时按目标项目授权与规则处理 Git，不自动取得全局修改或发布权限。

### 增强代码审查

`$personal-dev:review` / `/personal-dev:review` 仅在用户显式调用时运行。默认检查当前项目全部自有代码，包括已提交存量和工作区源码，即使没有 diff；指定目录、文件、模块、主题、commit 或 diff 时严格限定范围。它不依赖 Git，也不会启动原生 `/review`。

主模型在正式派发前一次性核对项目规则、范围、源码可读性、改动基线、报告位置与当前 Harness adapter。Codex 另核对可靠模型身份、当前派发工具名单与强度及解释器；Claude 核对原生 Agent 与非 fork 子代理能力。缺少必需项时集中输出 `BLOCKED`；生产权限、凭证、配额或实时运行数据属于可选证据，缺少时仍可进行代码层审查，并把相关量化结论列为待运行验证。审查和复核的实际型号/强度会在派发前展示；必要的独立复核只针对 P0/P1 或实质争议。

默认报告写到项目 `docs/reviews/`，代码、配置和 Git 状态只读，审查过程不自动修复或提交。报告区分 `COMPLETE`、`PARTIAL`、`BLOCKED` 执行状态与 P0–P3 风险等级；发现问题不会让执行状态自动变成 `BLOCKED`。没有高等级发现也不代表项目绝对安全。

## Agent 管理工具

### 查找冲突

`resolve-conflicts` 按当前 Agent 的实际加载规则检查项目与全局来源，在对话中报告双方原文、位置、触发条件、影响及最小建议。它区分冲突、歧义、能力重叠和已有覆盖规则消解的差异。

全过程只读，不改配置、不禁用或卸载入口，也不创建报告文件。来源或加载状态不明时标记 `UNKNOWN`，扫描不完整时标记 `PARTIAL`。

### 检查更新

`check-updates` 支持 Codex、Claude Code 与 Kimi Code，只比较已记录的 repo / path / ref、精确 commit 和安装证据，不更新对象或更换来源。固定 commit 不跟随 main；版本字符串相同也不代表内容相同。

源码快照、Marketplace 快照和客户端安装副本分别报告。来源无法确认时标记 `UNKNOWN SOURCE`，证据不足时标记 `UNKNOWN` 或 `BLOCKED`。

需要实际更新时，维护仓库按[维护指南](maintenance.md#升级第三方-skill)同步，再按下方对应客户端步骤刷新安装副本。

### 配置项目

修改 Plugin 开关时，逐项指定完整 Plugin 身份及启用 / 禁用状态，例如：

```text
$agent-manager:configure-project 在当前项目禁用 frontend-dev@agent-marketplace，启用 testing-automation@agent-marketplace
```

Claude 使用 `/agent-manager:configure-project`。该入口只处理用户明确指定的项目操作：编辑 `AGENTS.md`、从准确来源安装 standalone Skill，或执行受支持的 Plugin 开关。它不推荐组合、不提交或推送用户项目。

#### 项目开关支持范围

以下版本范围仅针对 `configure-project` 的配置执行能力：

| 客户端与已验证版本 | 项目 Plugin 开关 | 写入位置 |
| --- | --- | --- |
| Codex `0.162.0-alpha.17.2`、`0.162.0-alpha.2` | 已安装的本地 Marketplace Plugin | `.codex/config.toml` |
| Claude Code `2.1.291`、`2.1.296` | 已安装的 Marketplace Plugin | `.claude/settings.json` |
| Kimi Code Desktop `1.0.4` | 暂不支持，整批 `BLOCKED` | 不写配置 |

三个客户端的**单个 Skill 项目开关均不支持**。未验证的 Codex / Claude 版本、目标缺失或歧义、配置损坏、有效项目层证据不足，以及 Codex 未受信任项目或 workspace-managed Plugin，均拒绝整批操作。Claude 的 `.claude/settings.local.json` 若对目标存在反向覆盖，也会整批拒绝。

standalone Skill 的项目安装与 Skill 开关不同：用户须指定准确来源和项目内目标，并通过当前 Harness 的加载目录、来源、重复、冲突及路径检查。已确认的发现目录为 Codex `.agents/skills/`、Claude `.claude/skills/`、Kimi `.kimi-code/skills/` 或 `.agents/skills/`；实际版本、项目配置和会话证据优先。复制所需资源并记录来源，不运行来源脚本或可能写用户 cache 的安装器。

项目 Plugin 安装当前没有 Codex、Claude Code 或 Kimi Code 的全写入均留在项目内的已验证契约，因此整批 `BLOCKED`。项目 Plugin 开关能力不能替代安装能力。

`AGENTS.md` 默认编辑项目 Git/workspace 根文件；只有明确指定时才处理子目录。先核实当前 Harness 的真实指令链和遮蔽关系：Codex 同目录 `AGENTS.override.md` 优先；Claude Code v2.1.277+ 按祖先 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`、版本与 Project instructions 设置选择是否加载；Kimi 按实际项目来源判断。用户指定编辑文件时可以改文件本身，但不会自动添加引用或声称当前会话已加载。

任何一个目标不受支持、冲突未解决或核心来源/加载证据缺失，整个混合批次都不写入。全局与项目外始终只读；保存后新会话或重新加载才能确认会话状态。详细边界见 [项目文件预检](../plugins/agent-manager/skills/configure-project/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/configure-project/references/codex-support.md)、[Claude](../plugins/agent-manager/skills/configure-project/references/claude-support.md) 与 [Kimi](../plugins/agent-manager/references/kimi.md)。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Codex

从 GitHub 添加 Marketplace，再安装需要的分类；下面列出 Codex 的全部六类，可按需选择：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add frontend-dev@agent-marketplace --json
codex plugin add backend-dev@agent-marketplace --json
codex plugin add testing-automation@agent-marketplace --json
codex plugin add agent-manager@agent-marketplace --json
codex plugin add personal-dev@agent-marketplace --json
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
claude plugin install personal-dev@agent-marketplace
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
| 不知道 Skill 是否自动执行 | handoff、三个管理入口和 personal-dev 仅手动；其他入口按任务匹配，启用不会自行执行 |
| 配置开关返回 BLOCKED | 查看具体原因及上方支持范围；安装成功不代表具备所有项目配置能力 |
| Kimi 出现重复 Skill | 检查是否同时安装整仓库聚合插件和分类插件 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[Kimi Plugins](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/plugins.md)、[Kimi Skills](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/skills.md)。
