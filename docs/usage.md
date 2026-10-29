# 使用手册

[返回首页](../README.md) · [维护指南](maintenance.md)

已经安装并启用 Marketplace 的用户，从日常调用开始；安装步骤用于首次安装、换电脑或更新副本。

当前支持 Codex、Claude Code、Antigravity CLI（agy）与 DeepSeek Harness 桌面版（dsh）。安装与作用域边界分别见 [agy 说明](#antigravity-cliagy)和 [dsh 桌面版说明](#deepseek-harness-桌面版dsh)。

产品目录共有 **4 个 Plugin**、**26 个 Skills**，四端产品清单一致；数量不代表当前会话已加载。

## 日常调用

在聊天中写明 Skill 和要完成的任务：

| 客户端 | 调用格式 | 示例 |
| --- | --- | --- |
| Codex | `$<plugin>:<skill>` | `$software-dev:vue 帮我实现这个组件` |
| Claude Code | `/<plugin>:<skill>` | `/software-dev:vue 帮我实现这个组件` |
| agy | `/<skill>`（以实际命令清单为准） | `/vue 帮我实现这个组件` |
| dsh 桌面版 | `/<skill>`（在 `/` 建议菜单选择或直接输入） | `/vue 帮我实现这个组件` |

可用入口以当前会话实际显示的清单为准。Skill 改名发布后，刷新客户端安装副本并开启新会话或重载 Plugin；旧完整调用名不作为别名保留。

**仅手动调用**：`setup-matt-pocock-skills`、`handoff`、`grill-with-docs`、`improve-codebase-architecture`、`to-spec`、`to-tickets`、`implement`、`implement-spec`、`retro`。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

例如在 Codex 中：

```text
$matt:handoff 整理当前进度，供新会话继续
```

## Skill 速查

| Plugin | Skill | 用途 | 调用方式 |
| --- | --- | --- | --- |
| matt | setup-matt-pocock-skills | 首次使用 Matt Pocock 工程 Skills 前，配置项目的问题跟踪方式、分诊标签与领域文档布局 | 用户主动（仅手动） |
| matt | handoff | 整理进度、决定和后续工作，供新会话接续 | 仅手动 |
| matt | diagnosing-bugs | 排查复杂 Bug、报错、故障和性能回归 | 任务匹配 / 手动 |
| matt | codebase-design | 使用深模块原则设计接口、确定可替换与可测试的边界 | 任务匹配 / 手动 |
| matt | grill-with-docs | 推敲方案或设计，并随讨论记录 ADR 与领域词汇 | 用户主动（仅手动） |
| matt | improve-codebase-architecture | 扫描架构改进机会，生成 HTML 报告后推敲选定方案 | 用户主动（仅手动） |
| matt | grilling | 逐轮提问以检验计划、决定或想法 | 依赖调用 / 上游任务匹配 / 手动 |
| matt | domain-modeling | 澄清领域术语，维护 GLOSSARY.md 与 ADR | 依赖调用 / 上游任务匹配 / 手动 |
| matt | tdd | 先确认测试边界，再逐项执行失败测试与最小实现的循环 | 任务匹配 / 手动 |
| matt | research | 从可信来源收集资料和 API 文档，形成研究记录 | 任务匹配 / 手动 |
| matt | writing-for-agents | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 | 任务匹配 / 手动 |
| matt | to-spec | 将已有讨论整理为 Spec | 仅手动 |
| matt | to-tickets | 大型需求拆成有阻塞关系的 Ticket | 仅手动 |
| matt | implement | 普通开发默认入口，按需 TDD，完成后 code-review | 仅手动 |
| matt | implement-spec | 大型多 Ticket 并行开发 | 仅手动 |
| matt | code-review | Standards / Spec 两轴代码审查 | 任务匹配 / 主链调用 / 手动 |
| matt | retro | 复盘 Agent 环境、工具与 token 浪费 | 仅手动 |
| common-workflow | find-skills | 按需求查找 Skill，了解能力与安装方式 | 任务匹配 / 手动 |
| software-dev | frontend-design | 指导新页面或改版的视觉风格、排版和细节 | 任务匹配 / 手动 |
| software-dev | web-design-guidelines | 审查 Web 界面、可访问性和交互规范 | 任务匹配 / 手动 |
| software-dev | vue | 基于 Vue 官方文档介绍 Vue 3 核心 API；项目级规则优先，例如项目规定使用 JavaScript 时遵循项目配置 | 任务匹配 / 手动 |
| software-dev | fastapi | 指导 FastAPI 应用与 API 开发实践 | 任务匹配 / 手动 |
| software-dev | java-springboot | 指导 Spring Boot 的 REST API、数据访问、安全认证与测试 | 任务匹配 / 手动 |
| engineering-tools | docker-build-strategies | 指导 Docker 镜像构建与缓存策略 | 任务匹配 / 手动 |
| engineering-tools | docker-compose-patterns | 指导 Compose 服务依赖、健康检查、卷、网络与开发覆盖配置 | 任务匹配 / 手动 |
| engineering-tools | playwright-cli | 通过 Playwright CLI 操作浏览器并验证交互 | 任务匹配 / 手动 |

`grill-with-docs` 调用 `grilling` + `domain-modeling`；`improve-codebase-architecture` 调用 `codebase-design` + `grilling` + `domain-modeling`。这些依赖全部在同一 Plugin，安装 `common-workflow` 即包含完整目录和资源。`grill-me` 仅调用 `grilling`。三个入口保留上游的 `disable-model-invocation: true` 与 `allow_implicit_invocation: false`；依赖保留上游可由模型调用的策略与描述，不额外限制其触发条件。

`setup-matt-pocock-skills` 同样保留上游仅手动调用策略，用于初始化目标项目的工程 Skill 配置；先检查现状并确认草稿，再写入问题跟踪与领域文档约定。仅在目标项目已安装 `triage` 时配置分诊标签。安装此 Skill 不会自动运行初始化；执行时遵守目标项目规则，例如本仓库的 `CLAUDE.md` 仅导入 `AGENTS.md`。

`java-spring-boot` 已替换为 GitHub `awesome-copilot` 的 `java-springboot`，调用名同步改为 `$software-dev:java-springboot` / `/software-dev:java-springboot`。

`webapp-testing` 与 `dev-yagni` 已移除：网页操作与验证可使用 `playwright-cli`；长期维护 Playwright 测试时，可将专用测试规范配置在对应项目中，普通开发直接按项目规则执行。


## Matt 精选工作流

首次在目标项目使用工程主链前，显式调用 `$matt:setup-matt-pocock-skills`（Claude：`/matt:setup-matt-pocock-skills`），配置 issue tracker 与领域文档。整个目录含 GitHub / GitLab / 本地 Markdown tracker、domain 与 triage 模板；未安装 triage 时，上游 setup 跳过其标签配置，不需要引入 triage Skill。

注意：`to-spec` 和 `to-tickets` 仍要求标签约定，并使用 `ready-for-agent`。未安装 triage 时，需在目标项目的 issue tracker 配置中明确该标签的使用方式；GitHub / GitLab 项目还需确认目标标签已存在或按授权创建。本仓库的本地 Markdown 约定已记录在 [issue-tracker.md](agents/issue-tracker.md)。

| 场景 | 推荐入口 |
| --- | --- |
| 需求澄清 | `$matt:grill-with-docs` |
| 需求整理 | `$matt:to-spec` |
| 大型需求拆分 | `$matt:to-tickets` |
| 普通开发（默认） | `$matt:implement` |
| 大型并行开发 | `$matt:implement-spec` |
| 困难 Bug | `$matt:diagnosing-bugs` |
| 代码审查 | `$matt:code-review` |
| Agent 工作环境复盘 | `$matt:retro` |

日常按 `grill-with-docs → to-spec → 按需 to-tickets → implement` 使用，不强制每次拆 Ticket。`implement-spec` 仅用于大型、多 Ticket 且适合多 Agent 并行的任务，不作为普通开发默认入口。Claude 前缀用 `/matt:`；agy / dsh 以实际发现的 `/skill-name` 为准。

运行依赖：`grill-with-docs → grilling + domain-modeling`；`implement → tdd + code-review`；`tdd → codebase-design`（接口 / seam 设计时）；`implement-spec → tdd + code-review`（消费 Spec / Ticket，需 tracker 配置）；`improve-codebase-architecture → codebase-design + grilling + domain-modeling`；`retro → writing-for-agents`。to-spec、to-tickets、code-review、implement-spec 在缺少项目配置时提示运行 setup。

`handoff` 用于换 Harness / 上下文、跨目录与交接；诊断、研究、架构改进和文档工具独立使用。`retro` 仅手动触发，不加到默认开发完成流程。清单不包含 ask-matt、grill-me、triage、wayfinder、prototype、pr、wizard、teach、to-questionnaire、wait-what 或 in-progress / misc / deprecated。模板中出现这些名称不构成运行依赖。

每个选定目录完整同步，保留上游 agents、模板及相对引用文件；没有自定义 wrapper、worker/reviewer 路由或客户端 adapter。上游 implement 自身会在完成后调用 code-review，其审查流程仍按 upstream 原文执行。

上游 `implement` 要求执行完整测试、调用 `code-review`，然后提交当前分支；是否执行提交仍遵循用户授权和项目规则。`code-review` 使用 `git diff <fixed-point>...HEAD`，默认通过并行子代理审查，有 Spec 时审查标准与需求两方面；它需要一个比较基准，且该命令不包含暂存或未提交的工作区改动。因此，调用发生在提交前时，不能仅凭该审查声称未提交改动已被覆盖。完整测试和并行审查也应计入普通任务的时间与 token 成本。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Antigravity CLI（agy）

agy 产品目录包含四个 Plugin、26 个 Skills。同步使用本仓库项目 Skill：Codex `$sync-agy`，Claude Code / agy `/sync-agy`。它只服务仓库维护，不进入产品目录或全局 Skills。

在仓库根也可直接运行 PowerShell 7 脚本：

```powershell
# 只读检查，不安装
pwsh -NoProfile -File .agents/skills/sync-agy/scripts/sync.ps1 -CheckOnly
# 安装或刷新当前工作区的全部产品插件到 agy 全局
pwsh -NoProfile -File .agents/skills/sync-agy/scripts/sync.ps1
```

脚本使用原生 `agy plugin validate / install / list / disable`；默认从 PATH 查找，Windows 可回退到 `%LOCALAPPDATA%/agy/bin/agy.exe`，也可显式传 `-AgyPath`。它不执行 Git pull、不改其他客户端配置，保留其他来源的插件与已有禁用状态。当前产品全部核验后，脚本识别当前用户默认插件目录 `~/.gemini/config/plugins/` 中 manifest 确认属于本仓库、但已不在 catalog 的旧插件，停用并将安装目录移入回收站；其他路径或无法确认来源的插件保留。只读预检会列出待回收项，不做修改。仓库内容更新后重复同步即可刷新安装副本；不是实时同步。

安装后开启新 agy 会话或按客户端提供的入口重载，确认 `/vue`、`/implement`、`/retro` 等命令。手动 Skills 仍需明确调用；不要仅凭 frontmatter 声称客户端已强制门控。静态校验、安装清单及资源一致性不代表已运行真实模型、SSH 或子代理业务流程。

### DeepSeek Harness 桌面版（dsh）

桌面版通过自带的文件系统 Skill provider 加载四个产品包的共享 Skills 与完整资源。同步不按版本号拦截，但会使用已安装桌面版的原生加载器校验实际兼容性。项目同步入口为 Codex `$sync-dsh`、Claude Code / agy `/sync-dsh`，不进入产品目录。这里使用已安装的桌面版，无需 npm CLI。

在仓库根按项目规则核验 `mise current`、`python --version`（3.12+）及 uv，再运行；`--desktop-path` 使用实际安装路径：

```powershell
# 只读预检
uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe" --check-only
# 同步或刷新
uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe"
```

脚本复用已有 PyYAML 6.x，通过 uv 隔离安装；不修改项目依赖或系统运行时。默认数据根是 `DSH_HOME` 或 `~/.dsh`，可用 `--dsh-home` 指定。必须先启动过桌面版以初始化 `profiles/desktop`。

内容放入 `~/.dsh/marketplaces/agent-marketplace/releases/<摘要>/plugins/`，保留包内相对路径、许可证及手动调用策略；`profiles/desktop/cordis.patch.yml` 仅维护带标记的 `agent-marketplace-skills` provider。已有设置、第三方扩展和默认 Skills 根保留，旧内容快照保留；用户同名 Skills、手改快照或并发配置修改会阻止覆盖。每次同步是显式刷新，不做后台自动同步，也不注册四个 npm 扩展。

同步后重开桌面版，在 `/` 建议菜单确认 `/vue`、`/implement`、`/retro` 等入口。`disable-model-invocation: true` 的 Skills 只通过用户直接输入 `/name` 注入。隔离验证会使用桌面版真实 provider 读取清单和正文，但不启动 Host 或模型，因此当前会话注入、SSH 和子代理业务执行仍需分别验证。

### Codex

从 Gitee 添加 Marketplace，再安装需要的分类；下面列出 Marketplace 中的四个 Plugin，可按需选择：

```powershell
codex plugin marketplace add git@gitee.com:vsattce/agent-marketplace.git --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add matt@agent-marketplace --json
codex plugin add software-dev@agent-marketplace --json
codex plugin add engineering-tools@agent-marketplace --json
```

安装后默认启用，可在 UI 中单独启用或禁用整个分类。新建聊天加载入口；界面未刷新时重开客户端。

本地开发可用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。用 `codex plugin marketplace list` 核对注册，`codex plugin list --marketplace agent-marketplace --available --json` 查看可安装入口；切换同名市场来源前先核对旧注册。

**刷新**：本地来源同步后，重新执行对应的 `codex plugin add <plugin>@agent-marketplace --json`。Gitee 来源先执行 `codex plugin marketplace upgrade agent-marketplace` 刷新客户端中的 Marketplace 快照，再重新安装对应 Plugin，最后新建聊天。

### Claude Code

从 Gitee 添加并按需安装分类：

```powershell
claude plugin marketplace add git@gitee.com:vsattce/agent-marketplace.git
claude plugin install common-workflow@agent-marketplace
claude plugin install matt@agent-marketplace
claude plugin install software-dev@agent-marketplace
claude plugin install engineering-tools@agent-marketplace
```

安装默认 user scope；仅某个项目需要时，使用 `claude plugin install <plugin>@agent-marketplace --scope project`。可用 `claude plugin list --json` 或 `claude plugin details <plugin>` 查看安装信息。

本地开发使用 `claude plugin marketplace add E:\WorkSpace\agent-marketplace`。当前已验证版本的本地目录来源直接加载源目录，编辑后新建会话或执行 `/reload-plugins`。

**刷新 Gitee 来源**：先更新市场，再更新需要的 Plugin，例如：

```powershell
claude plugin marketplace update agent-marketplace
claude plugin update software-dev@agent-marketplace
```

其他分类同理，完成后新建会话。切换同名市场来源前先核对注册；移除 Marketplace 会同时卸载其插件。

**从旧开发 Plugin 迁移**：刷新 Marketplace 本身不会移除已安装的 `frontend-dev` 或 `backend-dev` 副本。先安装 `software-dev@agent-marketplace`，确认新入口可用后，再用客户端原生流程分别禁用或卸载旧 Plugin；不要手动编辑全局配置或安装缓存。Codex 可运行 `codex plugin remove frontend-dev@agent-marketplace` 与 `codex plugin remove backend-dev@agent-marketplace`；Claude Code 可运行 `claude plugin uninstall frontend-dev@agent-marketplace` 与 `claude plugin uninstall backend-dev@agent-marketplace`。新入口示例：Codex `$software-dev:fastapi`、Claude Code `/software-dev:fastapi`。

**Playwright Plugin 迁移**：`testing-automation` 已并入 `engineering-tools`。刷新 Marketplace 不会卸载 Codex / Claude 的旧副本；已安装旧包时，先用客户端原生流程卸载，再安装或刷新 `engineering-tools@agent-marketplace`，避免重复发现 `playwright-cli`。Codex 使用 `codex plugin remove testing-automation@agent-marketplace`；Claude Code 使用 `claude plugin uninstall testing-automation@agent-marketplace`（项目或 local 安装需选择原作用域）。新调用为 Codex `$engineering-tools:playwright-cli`、Claude Code `/engineering-tools:playwright-cli`，任务匹配策略与上游内容不变。agy 同步会在来源可确认时自动停用并回收旧包，同步后仍用 `/playwright-cli`；无法确认来源时会停止并保留旧包。dsh 重新执行 `$sync-dsh` 后，现有 provider 切换到新快照中的四个产品目录，旧快照保留，仍用 `/playwright-cli`。本仓库变更不会自动迁移日常客户端安装。

**Matt 迁移**：先安装 matt，再刷新 common-workflow，重载或新建聊天，确认旧 common-workflow Matt 副本不再被发现。Matt 调用前缀改为 `$matt:` / `/matt:`，common-workflow 仅留 find-skills。仓库迁移不自动刷新日常全局安装；agy / dsh 仍通过各自现有显式同步入口刷新完整产品目录。

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 仓库已更新，客户端仍是旧内容 | 按对应客户端刷新安装副本，再新建会话 |
| 已安装，但当前聊天找不到入口 | 核对启用状态和当前会话清单，重新加载或新建聊天；磁盘存在不等于会话可用 |
| 不知道 Skill 是否自动执行 | 仅手动调用的入口见[日常调用](#日常调用)；其他入口可按任务匹配，启用不会自行执行 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)。
