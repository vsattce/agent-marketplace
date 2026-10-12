# 使用手册

[返回首页](../README.md) · [维护指南](maintenance.md)

已经安装并启用 Marketplace 的用户，从日常调用开始；安装步骤用于首次安装、换电脑或更新副本。

当前支持 Codex 与 Claude Code；其他客户端暂不适配或维护。

当前共 **6 个 Plugin、22 个 Skills**：四个第三方聚合 Plugin 收录 14 个 Skills；本仓库自有的 `agent-manager` 与 `personal-dev` 分别包含 3 个和 5 个 Skills。第三方来源、作者与许可证边界见 [README](../README.md)。

## 日常调用

在聊天中写明 Skill 和要完成的任务：

| 客户端 | 调用格式 | 示例 |
| --- | --- | --- |
| Codex | `$<plugin>:<skill>` | `$software-dev:vue-best-practices 帮我实现这个组件` |
| Claude Code | `/<plugin>:<skill>` | `/software-dev:vue-best-practices 帮我实现这个组件` |

可用入口以当前会话实际显示的清单为准。Skill 改名发布后，刷新客户端安装副本并开启新会话或重载 Plugin；旧完整调用名不作为别名保留。

**仅手动调用**：`handoff`、`am-conflict`、`am-update`、`am-config`，以及 `personal-dev` 中的 Skills。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

例如在 Codex 中：

```text
$common-workflow:handoff 整理当前进度，供新会话继续
$agent-manager:am-conflict 检查当前项目与全局规则的冲突
$agent-manager:am-update 检查已记录来源和安装副本是否有更新
```

## Skill 速查

| Plugin | Skill | 用途 | 调用方式 |
| --- | --- | --- | --- |
| common-workflow | handoff | 整理进度、决定和后续工作，供新会话接续 | 仅手动 |
| common-workflow | diagnosing-bugs | 排查复杂 Bug、报错、故障和性能回归 | 任务匹配 / 手动 |
| common-workflow | research | 从可信来源收集资料和 API 文档，形成研究记录 | 任务匹配 / 手动 |
| common-workflow | writing-for-agents | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 | 任务匹配 / 手动 |
| common-workflow | find-skills | 按需求查找 Skill，了解能力与安装方式 | 任务匹配 / 手动 |
| software-dev | frontend-design | 指导新页面或改版的视觉风格、排版和细节 | 任务匹配 / 手动 |
| software-dev | web-design-guidelines | 审查 Web 界面、可访问性和交互规范 | 任务匹配 / 手动 |
| software-dev | vue-best-practices | 指导 Vue、Vue Router、Pinia 和 Vite 开发实践 | 任务匹配 / 手动 |
| software-dev | fastapi | 指导 FastAPI 应用与 API 开发实践 | 任务匹配 / 手动 |
| software-dev | java-spring-boot | 指导 REST API、安全认证、数据访问与 Actuator | 任务匹配 / 手动 |
| engineering-tools | docker-build-strategies | 指导 Docker 镜像构建与缓存策略 | 任务匹配 / 手动 |
| testing-automation | webapp-testing | 验证本地网页交互，查看截图与控制台日志 | 任务匹配 / 手动 |
| testing-automation | playwright-cli | 通过 Playwright CLI 操作浏览器并验证交互 | 任务匹配 / 手动 |
| testing-automation | playwright-best-practices | 指导 Playwright 测试、模拟、认证、调试与 CI | 任务匹配 / 手动 |
| agent-manager | am-conflict | 只读查找项目与全局指令、Skill、Plugin 的冲突和歧义 | 仅手动 |
| agent-manager | am-update | 只读比较既定来源、仓库、安装副本与 Marketplace 状态 | 仅手动 |
| agent-manager | am-config | 预检后编辑项目指令、安装指定 Skill 或执行受支持的 Plugin 开关 | 仅手动 |
| personal-dev | dev-delegate | 主模型安排任务，独立编码与验收代理执行，主模型最终整体检查；Codex / Claude Code | 仅手动 |
| personal-dev | dev-review | 只读审查当前项目或明确范围，独立复核高等级发现并生成报告；Codex / Claude Code | 仅手动 |
| personal-dev | dev-yagni | 按当前明确目标完成最小但完整的开发任务；只要求方案时等待确认 | 仅手动 |
| personal-dev | dev-simplify | 默认只读提出行为等价的精简建议，确认后再编辑 | 仅手动 |
| personal-dev | dev-runtime-check | 使用当前 Harness 原生 Shell / SSH 对指定远端主机、容器或服务取证；默认只读 | 仅手动 |

普通小任务直接在交接消息中处理，不要求创建文档。委派开发只有在需要跨步骤恢复或保留验收证据时才建立 `docs/personal-dev/tasks/<task-id>/` 记录；审查报告、长任务进度、远端诊断保存及临时文件的路径和边界见[任务产物位置](../plugins/personal-dev/references/artifacts.md)。

## 个人开发工具（Codex / Claude Code）

```text
$personal-dev:dev-delegate 实现当前需求，保留现有接口和范围外行为
$personal-dev:dev-delegate 实现当前需求，编码 medium，验收 xhigh
$personal-dev:dev-review 检查当前项目的性能、资源、请求、磁盘和长期运行风险
$personal-dev:dev-yagni 按当前明确需求实现最小完整结果
$personal-dev:dev-simplify 检查当前 diff，先提出行为等价的精简建议
$personal-dev:dev-runtime-check 检查用户指定的远端主机和服务；默认只读
```

Claude Code 使用 `/personal-dev:dev-delegate` 与 `/personal-dev:dev-review`，未指定时沿用当前子代理模型与思考配置，省略 `model` / `effort`；用户明确指定时按本轮原生工具能力核验，也不要求 Codex 的 Luna、`reasoning_effort` 或 Python 检查器。派发前显示模型策略；实际 ID 或强度无法确认时标 `UNKNOWN`，不冒充已验证值。独立验收、两轮修复上限与主模型终审流程和 Codex 相同。

新入口调用名为 `/personal-dev:dev-yagni` 与 `/personal-dev:dev-simplify`。

主模型按可独立验证的功能或修复点拆任务，同类小改动合并。Codex 当前已确认的低成本编码系列为 Luna：从本轮派发工具实际允许的型号中选择与主模型同一大版本内数字版本最高者，默认 `xhigh` 编码；另一个干净上下文的同型号代理默认 `max`（最强）验收。用户可分别指定本次编码与验收强度，明确指定的值优先，未指定的角色保留默认值，无需再次确认强度；不支持的值会说明原因并中断。最终由当前主模型检查累计改动与跨任务联动。

Codex 需要本轮可靠的主模型身份、当前派发工具允许名单和支持强度信息。6.1 / 6.2 主模型可以用 6 Luna；7 主模型不能自动回退到 6 或 5.6。信息缺失、陌生命名、版本歧义、强度不支持或工具不能覆写时输出具体原因并中断。用户明确确认精确替代型号后可用于当前任务；持久接纳新系列需另行维护，不凭升级推荐或价格猜测选模型。

编码开始前一定先显示实际结果，例如：

```text
编码模型：gpt-6-luna｜思考强度：xhigh
验收模型：gpt-6-luna｜思考强度：max
```

成功后直接执行，不额外确认是否开始。用户可明确覆写型号或强度；有变化先重新显示。独立验收检查需求、实现、相关调用点和验证证据，阻塞问题完整汇总，风格建议不扩大返工。初次实现后每个任务累计最多两轮修复，第二轮复验仍阻塞则全流程停止，由用户决定升级；主模型不自动接手编码。终审修复沿用相应任务剩余次数。

Codex 随 Skill 提供的 Python 标准库检查器只校验主模型根据当前工具整理的模型信息，不连接服务、不验证输入来源、不修改配置，也不是原生派发工具的强制拦截器。使用已有且符合规则的 Agent 工具解释器；缺少环境时中断，不自动安装或切换。费用与 Codex 额度的实际节省需要实测，不按 API 标价推算固定比例。

### 按需实现与精简

`dev-yagni` 与 `dev-simplify` 均只在用户显式调用后运行。调用 `dev-yagni` 时，只要目标清楚且用户没有要求只读讨论或暂缓修改，就由当前模型默认完成最小但完整的实现；用户只要求方案时，先说明方案并等待确认。按真实适用性优先复用项目已有能力和依赖，再考虑标准库或成熟的第三方依赖。需要新依赖时，按目标项目规则说明必要性、替代方案与维护代价；安装或升级依赖遵循当前任务已有授权和项目规则，调用 Skill 本身不增加权限。

调用 `dev-simplify` 后默认由当前模型只读检查并提出行为等价的精简建议，等待确认后编辑；用户明确要求直接精简时执行。默认范围是当前项目工作区的暂存、未暂存和新增源码；用户只写 Skill 名称时仍先检查该 diff。只有 Git 不可用或没有 diff、且未指定范围时才询问，不猜最近提交或扩大到全项目。Bug 单独报告，修复需另行明确授权。

两个 Skill 只作用于当前调用指向的项目和任务，不跨项目、不修改全局配置；任务结束或用户明确更换任务后不继续生效。`dev-simplify` 默认不自行派生代理或调用其他 Skill；用户明确选择 `dev-delegate` 时，才将已启用约束、已确认建议、授权范围和验证条件交给既有流程，尚待确认的建议仍需等待确认。

调用 Skill 本身不扩大 Git、依赖或发布权限；这些操作按目标项目规则和当前任务已有授权处理。若组合使用两个 Skill，Codex CLI `0.162.0-alpha.17.2` 实测同一消息内的两个显式入口都会加载；Claude Code `2.1.296` 同一消息只直接加载第一个入口。Claude Code 上请在后续消息中再显式调用另一个 Skill；不要把同消息并列调用当作双入口均已加载的保证。

Codex / Claude 均注册此 Plugin。安装后新建对应客户端会话加载；仓库有文件或已经推送，不代表当前会话已注入新 Skill。该 Skill 执行时按目标项目授权与规则处理 Git，不自动取得全局修改或发布权限。

### 增强代码审查

`$personal-dev:dev-review` / `/personal-dev:dev-review` 仅在用户显式调用时运行。默认检查当前项目全部自有代码，包括已提交存量和工作区源码，即使没有 diff；指定目录、文件、模块、主题、commit 或 diff 时严格限定范围。它不依赖 Git，也不会启动原生 `/review`。

主模型在正式派发前一次性核对项目规则、范围、源码可读性、改动基线、报告位置与当前 Harness adapter。Codex 另核对可靠模型身份、当前派发工具名单与强度及解释器；Claude 核对原生 Agent 与非 fork 子代理能力。缺少必需项时集中输出 `BLOCKED`；生产权限、凭证、配额或实时运行数据属于可选证据，缺少时仍可进行代码层审查，并把相关量化结论列为待运行验证。审查和复核的实际型号/强度会在派发前展示；必要的独立复核只针对 P0/P1 或实质争议。

默认报告写到项目 `docs/personal-dev/reviews/<review-id>/report.md`，长审查的轻量进度记录与报告同目录。代码、配置和 Git 状态只读，审查过程不自动修复、提交或推送。报告区分 `COMPLETE`、`PARTIAL`、`BLOCKED` 执行状态与 P0–P3 风险等级；发现问题不会让执行状态自动变成 `BLOCKED`。没有高等级发现也不代表项目绝对安全。

### 远端运行诊断

`$personal-dev:dev-runtime-check` / `/personal-dev:dev-runtime-check` 仅在用户显式调用时运行。需要目标主机、SSH 连接方式、诊断对象和相关时间范围；信息足够时直接开始取证。默认只读并在聊天中汇报；只有用户明确要求保存时，才写入项目 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。明确要求修复后才执行授权范围内的必要操作，并遵守当前 Harness 的权限与审批。

Codex 使用其原生终端能力，Claude Code 使用原生 Bash 工具。诊断直接连接用户指定目标，先确认主机与进程、服务或容器身份；连接或命令失败时停止远端结论，不改查当前工作站。连接和每条远端命令都设置有限超时，仅对适用的暂时性错误有限重试。按症状有限采样，比较速率时记录两次计数、单位和真实间隔，并区分宿主机、容器与应用。排查请求量时区分浏览器到自有后端和后端到第三方；部署时间与故障相邻只表示相关性，不单独证明因果。不得记录凭据或启动长期采集。

## Agent 管理工具

### 查找冲突

`am-conflict` 仅支持 Codex 与 Claude Code；它按对应客户端的实际加载规则检查项目与全局来源，在对话中报告双方原文、位置、触发条件、影响及最小建议。它区分冲突、歧义、能力重叠和已有覆盖规则消解的差异。其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。

全过程只读，不改配置、不禁用或卸载入口，也不创建报告文件。来源或加载状态不明时标记 `UNKNOWN`，扫描不完整时标记 `PARTIAL`。

### 检查更新

`am-update` 支持 Codex 与 Claude Code，只比较已记录的 repo / path / ref、精确 commit 和安装证据，不更新对象或更换来源，也不创建报告文件。其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。固定 commit 不跟随 main；版本字符串相同也不代表内容相同。

源码快照、Marketplace 快照和客户端安装副本分别报告。来源无法确认时标记 `UNKNOWN SOURCE`，证据不足时标记 `UNKNOWN` 或 `BLOCKED`。

需要实际更新时，维护仓库按[维护指南](maintenance.md#升级第三方-skill)同步，再按下方对应客户端步骤刷新安装副本。

### 配置项目

修改 Plugin 开关时，逐项指定完整 Plugin 身份及启用 / 禁用状态，例如：

```text
$agent-manager:am-config 在当前项目禁用 software-dev@agent-marketplace，启用 testing-automation@agent-marketplace
```

Claude 使用 `/agent-manager:am-config`。该入口只处理用户明确指定的项目操作：编辑 `AGENTS.md`、从准确来源安装 standalone Skill，或执行受支持的 Plugin 开关。它不推荐组合、不提交或推送用户项目。

#### 项目开关支持范围

以下版本范围仅针对 `am-config` 的配置执行能力：

| 客户端与已验证版本 | 平台 | 项目 Plugin 开关 | 写入位置 |
| --- | --- | --- | --- |
| Codex `0.162.0-alpha.17.2`、`0.162.0-alpha.2` | Windows | 已安装的本地 Marketplace Plugin | `.codex/config.toml` |
| Claude Code `2.1.291`、`2.1.296` | Windows | 已安装的 Marketplace Plugin | `.claude/settings.json` |

Plugin 开关编辑器在其他操作系统返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`；这不限制 `AGENTS.md` 编辑或 standalone Skill 安装。Codex 与 Claude Code 的**单个 Skill 项目开关均不支持**。其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。未验证的 Codex / Claude 版本、目标缺失或歧义、配置损坏、有效项目层证据不足，以及 Codex 未受信任项目或 workspace-managed Plugin，均拒绝整批操作。Claude 的 `.claude/settings.local.json` 若对目标存在反向覆盖，也会整批拒绝。

standalone Skill 的项目安装与 Skill 开关不同：用户须指定准确来源和项目内目标，并通过当前 Harness 的加载目录、来源、重复、冲突及路径检查。已确认的发现目录为 Codex `.agents/skills/` 和 Claude Code `.claude/skills/`。复制所需资源并记录来源，不运行来源脚本或可能写用户 cache 的安装器。

项目 Plugin 安装当前没有 Codex 或 Claude Code 的全写入均留在项目内的已验证契约，因此整批 `BLOCKED`。项目 Plugin 开关能力不能替代安装能力。

`AGENTS.md` 默认编辑项目 Git/workspace 根文件；只有明确指定时才处理子目录。先核实当前 Harness 的真实指令链和遮蔽关系：Codex 同目录 `AGENTS.override.md` 优先；Claude Code v2.1.277+ 按祖先 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`、版本与 Project instructions 设置选择是否加载。用户指定编辑文件时可以改文件本身，但不会自动添加引用或声称当前会话已加载。

任何一个目标不受支持、冲突未解决或核心来源/加载证据缺失，整个混合批次都不写入。全局与项目外始终只读；保存后新会话或重新加载才能确认会话状态。详细边界见 [项目文件预检](../plugins/agent-manager/skills/am-config/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/am-config/references/codex-support.md) 与 [Claude](../plugins/agent-manager/skills/am-config/references/claude-support.md)。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Codex

从 GitHub 添加 Marketplace，再安装需要的分类；下面列出 Marketplace 中的六个 Plugin，可按需选择：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add software-dev@agent-marketplace --json
codex plugin add engineering-tools@agent-marketplace --json
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
claude plugin install software-dev@agent-marketplace
claude plugin install engineering-tools@agent-marketplace
claude plugin install testing-automation@agent-marketplace
claude plugin install agent-manager@agent-marketplace
claude plugin install personal-dev@agent-marketplace
```

安装默认 user scope；仅某个项目需要时，使用 `claude plugin install <plugin>@agent-marketplace --scope project`。可用 `claude plugin list --json` 或 `claude plugin details <plugin>` 查看安装信息。

本地开发使用 `claude plugin marketplace add E:\WorkSpace\agent-marketplace`。当前已验证版本的本地目录来源直接加载源目录，编辑后新建会话或执行 `/reload-plugins`。

**刷新 GitHub 来源**：先更新市场，再更新需要的 Plugin，例如：

```powershell
claude plugin marketplace update agent-marketplace
claude plugin update software-dev@agent-marketplace
```

其他分类同理，完成后新建会话。切换同名市场来源前先核对注册；移除 Marketplace 会同时卸载其插件。

**从旧开发 Plugin 迁移**：刷新 Marketplace 本身不会移除已安装的 `frontend-dev` 或 `backend-dev` 副本。先安装 `software-dev@agent-marketplace`，确认新入口可用后，再用客户端原生流程分别禁用或卸载旧 Plugin；不要手动编辑全局配置或安装缓存。Codex 可运行 `codex plugin remove frontend-dev@agent-marketplace` 与 `codex plugin remove backend-dev@agent-marketplace`；Claude Code 可运行 `claude plugin uninstall frontend-dev@agent-marketplace` 与 `claude plugin uninstall backend-dev@agent-marketplace`。新入口示例：Codex `$software-dev:fastapi`、Claude Code `/software-dev:fastapi`。

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 仓库已更新，客户端仍是旧内容 | 按对应客户端刷新安装副本，再新建会话 |
| 已安装，但当前聊天找不到入口 | 核对启用状态和当前会话清单，重新加载或新建聊天；磁盘存在不等于会话可用 |
| 不知道 Skill 是否自动执行 | handoff、三个管理入口和 personal-dev 仅手动；其他入口按任务匹配，启用不会自行执行 |
| 配置开关返回 BLOCKED | 查看具体原因及上方支持范围；安装成功不代表具备所有项目配置能力 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)。
