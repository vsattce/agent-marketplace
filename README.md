# agent-marketplace

个人使用的 Skill / Plugin 集合，Codex 中显示为 **Agent Marketplace**。四个第三方聚合 Plugin（13 个已选定 Skills）加一个本仓库直接维护的 OWNED Plugin（2 个 Skills），共五个 Plugin、15 个 Skills。作者、GitHub 仓库和 upstream 只作为来源信息，不决定分类。

当前先完成 Codex。Skill 内容作为共享核心，其他 Agent 的 manifest / adapter 后续单独增加；本轮没有实现 Claude Code、Kimi Code 或 Antigravity 适配。

## Plugin

| Plugin 标识 | 中文名称与简介 | Skills |
| --- | --- | --- |
| `common-workflow@agent-marketplace` | **通用工作流**：任务交接、问题诊断、资料研究与 Agent 工作流工具。 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `frontend-dev@agent-marketplace` | **前端开发**：前端界面设计、Vue 开发与 Web 设计规范。 | frontend-design、web-design-guidelines、vue、vue-best-practices |
| `backend-dev@agent-marketplace` | **后端开发**：Java / Spring Boot 开发与工程实践。 | java-spring-boot |
| `testing-automation@agent-marketplace` | **测试与自动化**：网页测试、Playwright 浏览器自动化与测试最佳实践。 | webapp-testing、playwright-cli、playwright-best-practices |
| `agent-manager@agent-marketplace`（OWNED） | **Agent 管理工具**：当前项目冲突整理与既定来源版本检查。 | resolve-conflicts、check-updates（均仅手动） |

默认继续使用已选定的第三方 Skill 和来源；新增第三方 Skill 优先归入四类，只有新的领域才考虑增加分类。自有 Plugin 直接维护，不走第三方同步。`resolving-merge-conflicts` 和第三方 standalone `pdf` 不保留，也没有 Legacy 入口。

### 各 Skill 的用途与触发方式

Plugin 的详情说明均列出所含 Skill 的用途与触发方式。**主动**表示 Codex 可在当前任务匹配 Skill 描述时自动选用；**被动**表示用户手动指定 Skill。两者是调用方式，启用插件不会自行执行任务，主动选用也不保证每次发生。

| Plugin | Skill（是什么） | 做什么 | 触发方式 |
| --- | --- | --- | --- |
| 通用工作流 | handoff（任务交接） | 将当前会话的进度、决定和后续工作整理成文档，供新会话继续。 | 被动：仅手动 |
| 通用工作流 | diagnosing-bugs（问题诊断） | 逐步排查复杂 Bug、报错、故障和性能回归，核验证据与原因。 | 主动：诊断任务；被动：手动 |
| 通用工作流 | research（资料研究） | 从可信来源收集资料和 API 文档，形成可追溯的研究记录。 | 主动：研究任务；被动：手动 |
| 通用工作流 | writing-for-agents（Agent 文档编写） | 创建或修改 Skill、AGENTS.md、CLAUDE.md 等供 Agent 使用的文档。 | 主动：Agent 文档任务；被动：手动 |
| 通用工作流 | find-skills（Skill 查找） | 按需求寻找可用 Skill，了解其能力与安装方式。 | 主动：查找 Skill 时；被动：手动 |
| 前端开发 | frontend-design（界面设计） | 新建或重塑前端页面，指导视觉风格、排版和界面细节。 | 主动：界面设计任务；被动：手动 |
| 前端开发 | web-design-guidelines（Web 界面审查） | 检查 UI 代码、可访问性和交互是否符合 Web 设计规范。 | 主动：界面审查任务；被动：手动 |
| 前端开发 | vue（Vue 3 开发） | 指导组件、Composition API、响应式逻辑及内置组件的使用。 | 主动：Vue 开发任务；被动：手动 |
| 前端开发 | vue-best-practices（Vue 开发规范） | 指导 Vue 组件、Vue Router、Pinia 和 Vite 项目的实现与最佳实践。 | 主动：Vue 开发任务；被动：手动 |
| 后端开发 | java-spring-boot（Spring Boot 开发） | 指导 REST API、安全认证、数据访问及 Actuator 监控的实现。 | 主动：Spring Boot 开发任务；被动：手动 |
| 测试与自动化 | webapp-testing（网页测试） | 用 Playwright 验证本地网页交互，查看截图与控制台日志，排查界面问题。 | 主动：网页测试任务；被动：手动 |
| 测试与自动化 | playwright-cli（浏览器自动化） | 通过 Playwright CLI 打开网页、点击输入、读取快照和验证交互。 | 主动：浏览器操作或网页验证任务；被动：手动 |
| 测试与自动化 | playwright-best-practices（Playwright 测试实践） | 指导测试编写、定位器、断言、Fixture、模拟、认证、调试与 CI 配置。 | 主动：Playwright 测试任务；被动：手动 |
| Agent 管理工具 | resolve-conflicts（冲突整理） | 检测项目重复入口，验证项目层精确 path disable；不支持时 BLOCKED。 | 被动：仅手动 |
| Agent 管理工具 | check-updates（更新检查） | 只读比较既定 upstream、自有仓库、安装缓存与 Marketplace 状态。 | 被动：仅手动 |

在 Codex 中可用 `$<plugin>:<skill>` 手动指定，例如 `$common-workflow:handoff` 或 `$frontend-dev:vue`。handoff 的 upstream 明确设置 `allow_implicit_invocation: false`；其余第三方 Skill 未禁用隐式调用。agent-manager 的两个 Skill 同样明确设置该官方策略，并在 description 中声明 `Only use when explicitly invoked by the user.`。依据 [OpenAI 官方 Skill 调用说明](https://learn.chatgpt.com/docs/build-skills)，设为 false 后仍可显式调用，不进入默认自动选择上下文。

## 目录与维护入口

```text
agent-marketplace/
├── .agents/plugins/marketplace.json
├── sources.yaml
├── sources.lock.json
├── scripts/sync.py
├── tests/test_sync.py
├── plugins/
│   ├── common-workflow/
│   ├── frontend-dev/
│   ├── backend-dev/
│   ├── testing-automation/
│   └── agent-manager/             # OWNED，直接维护
│       ├── plugin.json
│       ├── references/codex.md
│       └── skills/
│           ├── resolve-conflicts/ # SKILL.md + agents/openai.yaml + scripts
│           └── check-updates/     # SKILL.md + agents/openai.yaml + scripts
└── README.md
```

每个 Plugin 包含根目录 `plugin.json`、`skills/<skill-name>/`；第三方 Plugin 另有 `licenses/<skill-name>/`。Plugin 根使用便携 manifest，中文信息位于 `extensions.com.openai.interface`；Marketplace 的 `skills: "./skills/"` 与原生目录发现指向同一组共享内容。

`sources.yaml` 是第三方来源唯一人工维护入口，只记录 group / displayName 及各 Skill 的 `name`、`repo`、`path`、`ref`。新增、移除、换源、换路径、分组或 ref 只编辑该文件，然后同步。`sources.lock.json` 自动记录来源、分类、实际同步 commit 和 UTC 同步时间，不参与版本选择。OWNED Plugin 不进入这两个文件。

第三方 `skills/` 内容由脚本原样同步，不人工修改；`.gitattributes` 禁止 Git 转换快照的换行，避免 Windows 检出后重复同步产生假变化。Skill 内许可证保持原样，upstream 仓库根的 LICENSE / NOTICE 等另存于 `licenses/<skill-name>/`。快照随仓库保存，换电脑通过 Plugin 安装恢复，无需向 `~/.codex/skills` 手工复制目录。

## 已确认来源

准确路径见 [sources.yaml](sources.yaml)，实际完整 commit 见 [sources.lock.json](sources.lock.json)。全部沿用重构前已确认的 upstream / path / ref 策略。

| upstream | Skills | ref |
| --- | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | handoff、diagnosing-bugs、research、writing-for-agents | `main` |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | find-skills | `main` |
| [anthropics/skills](https://github.com/anthropics/skills) | frontend-design、webapp-testing | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | web-design-guidelines | `main` |
| [antfu/skills](https://github.com/antfu/skills) | vue、vue-best-practices | `a74f281a27dadc02397bc1a174b0f2c97531b6ae` |
| [pluginagentmarketplace/custom-plugin-java](https://github.com/pluginagentmarketplace/custom-plugin-java) | java-spring-boot | `main` |
| [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) | playwright-cli | `main` |
| [currents-dev/playwright-best-practices-skill](https://github.com/currents-dev/playwright-best-practices-skill) | playwright-best-practices | `main` |

运行同步即表示更新到配置 ref 的当前内容，不询问是否升级、不比较作者或替换实现。`main` 获取最新内容，Anthropic / Vue 保留现有固定 commit；需要改变固定快照时直接编辑 `ref`。

本仓库自有脚本和 metadata 使用 MIT License，第三方内容遵守各自附带的 upstream 许可证。

## 同步

需要 Git、mise 管理的 Python 3.12+ 和 uv。使用 PyYAML 6.x 读取 YAML，依赖声明在脚本 PEP 723 metadata 中，通过 uv 隔离安装，不改全局环境。

在仓库根运行，先核对运行时：

```powershell
mise current
python --version
uv run --python (mise which python) --no-python-downloads --script scripts/sync.py
```

已有包含 PyYAML 的 Python 环境时，也可直接执行：

```powershell
python scripts/sync.py
```

脚本按 `repo + ref` 拉取 Git 快照，校验目录、`SKILL.md` 名称和描述，同步到配置指定 group，保留许可证，更新 lock，输出 commit 和文件增加 / 修改 / 移除数量。不会执行 upstream 脚本。

所有来源拉取和校验通过后才替换本地快照；普通写入失败会恢复本次替换前的快照及 lock。网络或 ref / path 失败时返回非零退出码，保留原有内容。相同 commit 且内容未变时保留同步时间，重复运行不产生 lock 差异；本地快照被误改或缺失时也能恢复。

脚本不推荐、不分类、不替换 upstream、不自动删除移出配置的 Skill，不安装 Plugin、不清理 standalone，也不 commit / push。同步单个 Skill 时会移除该快照中 upstream 已删除的旧文件；从配置移除整项时保留旧 Skill 和记录，并提示手工检查。

同步后检查 `git status --short`、`git diff --stat`、`git diff -- sources.lock.json`。首次生成的文件是 untracked，结合 status 查看。回退 upstream 内容时可将 `ref` 改为 lock 中记录的 commit，再运行同步。

没有 dependency resolver、semver 策略、自动分类、后台更新或 GitHub Actions 自动更新。

### Owned / Generated 边界

`scripts/sync.py` 的 `MANAGED_PLUGINS` 明确列出四个第三方聚合 Plugin。`sources.yaml` 不能自行授予其他目录同步权限；未知分组、包含非 Generated 项的 lock、Owned 目标、manifest 目标或重定向目录会在写入前失败。发布/回滚阶段再次校验，只允许写入 `plugins/<managed>/skills/<name>`、`plugins/<managed>/licenses/<name>` 与根目录 lock。脚本不遍历 Owned 目录做清理；新增自有 Plugin 直接维护源码，不改白名单。

### Agent 管理工具

使用 `$agent-manager:resolve-conflicts` 或 `$agent-manager:check-updates` 显式调用。两个入口均有 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`，无 onboarding、启动 hooks 或自动任务。本机 0.162.0-alpha.2 的裸 `$resolve-conflicts` / `$check-updates` 未注入 Plugin Skill 正文，使用带 Plugin namespace 的实际入口。安装缓存刷新及新聊天加载规则与其他 Plugin 一致；仓库可发现不代表当前聊天已经安装/加载。

resolve-conflicts 先可靠识别调用时项目根目录和当前 Harness，再用共享 Codex adapter 核验当前官方规范、trust 与配置层。按完全相同 Skill name 查重，比较 namespace / description / Plugin / scope；默认项目优先，用户指定来源优先。同名来源用实际加载 **path** 精确区分，不按 name 禁用。实际过滤验证须确认目标 global Skill 不再可用、项目同名 Skill 和 Plugin 其他 Skill 保留。通过后才无损增量修改当前项目 TOML；无法安全验证就 BLOCKED，不能算 RESOLVED。

**最高优先级红线：全局只读，当前项目可读写，项目外绝不写入。** 所有配置、临时文件、替换与失败清理均由 `write_path()` 校验调用项目及 canonical 路径；拒绝其他仓库、路径逃逸、用户配置禁区、symlink、Windows junction 和 hardlink。全局 Skill path 仅作为项目配置里的只读 selector。非项目目录立即拒绝，不初始化 Git、不创建配置。项目层无法解决时不回退到全局修改，也不禁用整个 Plugin。

**上一轮已验证限制：codex-cli 0.162.0-alpha.2 的项目 `.codex/config.toml` 中 `skills.config` 不参与该 Plugin Skill filtering。** 当时 `config/read` 可以看到规则，但 SKILL.md 路径和目录 selector 都没有屏蔽 global handoff；临时用户层对照有效。该历史结论不代替当前版本核验，旧验证方式也不能按新增红线再次执行。当前无法安全验证时输出 BLOCKED、已知版本与路径、失败原因，不写无效规则、不改用户配置、不关闭整个 Plugin。持久化隔离目前没有已验证 workaround；独立 Skill 同样必须验证项目层实际生效。

helper `project_config.py` 使用 tomlkit 0.13.x 保留 TOML 注释/格式，避免手工拼接或全文件重建；它是经过 adapter 核验后的底层编辑器，CLI 只做项目识别与只读预检。运行时使用已有依赖及 `python -B`，避免在全局 Plugin 内生成 bytecode 或触发项目外 uv 缓存/安装；无法满足就停止。运行 helper 前服从目标项目约束核对 mise 和 Python，不匹配时停止。

`probe_codex.py` 已改为只读路径/metadata 预检：**不启动 Codex、不安装测试 Plugin、不创建临时 CODEX_HOME 或项目外临时目录**。旧探测会在系统临时目录写文件，不符合新增红线；设置 CODEX_HOME 也不能保证所有子进程、日志和缓存受限。没有已验证的项目内进程约束时明确 BLOCKED，保留真实全局环境。它不能证明过滤成功；需要安全的当前版本行为证据才允许编辑项目规则。路径校验不是任意外部程序的系统级 sandbox。

check-updates 只读检查第三方 sources/lock、自有 Plugin 对应 Git 分支、Codex 安装 metadata、Marketplace snapshot 和非系统 standalone Skills。按已记录 repo/path/ref 比较精确 commit，固定 SHA 不跟随 main；OWNED 比较当前 branch/tracking remote 的实时 SHA 与 ancestry。缺失路径不删项；安装 version 相同不代表内容最新；来源、权限或版本证据不足分别 UNKNOWN / UNKNOWN SOURCE / BLOCKED，不搜索替代作者。输出版本表及 Latest / Updates available / Unknown 汇总，不更新任何对象，不 commit/push。

源码入口是 Skill 工作流和 `references/codex.md`；确定性 helper 负责项目/TOML安全边界、隔离兼容性探测以及第三方 API 比较。第一版只提供 Codex adapter，其他 Harness 返回 UNSUPPORTED AGENT。

## Codex 添加、安装与刷新

Marketplace 使用原生本地目录 source，五个入口指向 `./plugins/<plugin>`，路径相对于 Marketplace 仓库根。GitHub 来源也从市场快照的相对目录安装，不再逐张卡片下载 upstream。

换电脑恢复时，从已经发布的 GitHub 仓库安装：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add frontend-dev@agent-marketplace --json
codex plugin add backend-dev@agent-marketplace --json
codex plugin add testing-automation@agent-marketplace --json
codex plugin add agent-manager@agent-marketplace --json
```

本地开发使用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。同名 Marketplace 切换来源时，先用 `codex plugin marketplace list` 核对，再移除旧注册并添加目标来源。用 `codex plugin list --marketplace agent-marketplace --available --json` 查看入口。

安装后默认启用，可在 UI 单独 Enable / Disable 整个分类。新建聊天加载迁移后的名称；界面未刷新时重开客户端。调用标识例如 `$common-workflow:handoff`、`$frontend-dev:vue`、`$testing-automation:playwright-cli`。保持 upstream 策略：handoff 仅手动，其余按任务匹配，也可显式调用；启用不会自动执行。

同步只更新仓库，Codex 从安装缓存加载。本地同步后重复执行对应 `codex plugin add <group>@agent-marketplace --json` 刷新安装副本；GitHub 来源先刷新 Marketplace 再重新安装对应 Plugin。Plugin 不安装 Playwright / Java / Vue 运行依赖，使用时遵循目标项目环境约束。

## 第三方迁移验证与清理（前一轮）

2026-10-10，使用 `codex-cli 0.162.0-alpha.2` 在日常配置安装并启用四个 Plugin。仓库外新进程的 `skills/list` 发现 5 / 4 / 1 / 3 个指定 Skills，全部文件与仓库快照字节一致，中文 metadata 正确。新 Plugin 验证成功后，已用 Codex 原生命令卸载旧八个细粒度 Plugin，再次发现恰好 13 个目标 Skills，没有重复加载。

本轮开始时，以下 standalone 已不存在，完成后再次确认均不存在：`diagnosing-bugs`、`handoff`、`research`、`writing-for-agents`、`frontend-design`、`webapp-testing`、`vue`、`vue-best-practices`、`find-skills`、`web-design-guidelines`、`java-spring-boot`、`playwright`、`playwright-best-practices`、`resolving-merge-conflicts`、`pdf`。`~/.codex/skills` 仅剩 `.system`，非系统目录为零；系统 Skills 和其他市场未改动。

旧 `plugins/marketplace-smoke/` 只有空测试目录，无文件、manifest 或 Skill，不在 Git 或 Marketplace 中。自动审批检查拒绝了其递归和空目录删除，只返回 `blocked by policy`，因此空目录仍保留，不影响四个 Plugin。

以上验证覆盖安装、启用、metadata、发现和文件来源，没有逐个执行全部 Skill 内部开发流程，也没有用桌面截图验收卡片渲染。当前聊天的 Skill 列表是开始时注入的旧快照，迁移后的名称在新聊天加载。

同步工具测试：

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<0.14" python -B -m unittest discover -s tests -v
```

覆盖重复同步、快照恢复、upstream 内容更新、许可证保留、网络 / 目录失败不写入、非法路径与重名拒绝、替换失败恢复，以及不自动删除移出配置的 Skill。

本轮新增管理/边界测试位于 `tests/test_agent_manager.py` 和 `tests/test_codex_loader.py`。真实 Codex loader 测试为显式启用的隔离测试：

2026-10-10，上一轮完整执行 30 项测试全部通过（含当时 2 项真实 Codex loader 验证）。普通相关对话不注入两个手动 Skill 的 description / 正文；带 namespace 的两个显式入口均注入正文。此验收覆盖发现与调用策略，不代表已执行两个 Skill 的完整业务流程。新增边界测试验证项目内增量写入、全局 selector 只读、用户配置/Skill/Plugin/其他仓库拒写、路径逃逸、Windows 大小写/盘符、symlink/junction/hardlink 拒写，以及非项目和不受限探测 BLOCKED。

```powershell
$env:AGENT_MANAGER_CODEX_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<0.14" python -B -m unittest discover -s tests -v
Remove-Item Env:AGENT_MANAGER_CODEX_TESTS
```

loader 测试是独立开发验收，使用临时 CODEX_HOME、真实本机 Codex 和 localhost 请求捕获器，只验证发现/上下文注入，不调用真实模型或执行 Skill 正文；其进程工具已移到测试文件中，不随 Skill 执行，不能作为冲突处理 workaround。旧有系统临时目录 runtime filtering 测试已由零写入 BLOCKED 测试取代。上一轮同步集成验证按现有 13 项配置连续进行两次真实 upstream 同步，两次快照/lock 完全一致，agent-manager 源码 hash 保持不变；实际仓库 sources/lock 与第三方快照没有更新。第三方检查 helper 的实网 GitHub API 查询返回 HTTP 403，各项明确 UNKNOWN；LATEST / UPDATE AVAILABLE / 路径缺失等分支另以受控响应验证。

开发完成并通过必要验证后，按项目 AGENTS.md 默认提交并推送；Skill 执行流程本身不 commit / push。

本次边界强化验证：37 项测试，36 项通过，1 项真实 Codex loader 测试未启用；Windows symlink、junction、hardlink 和盘符/大小写检查均真实通过。项目 TOML 增量编辑验证的是文件边界与内容保留，未宣称当前 Codex 的项目级过滤已生效。

加载方式参考 [OpenAI Plugin 规范](https://developers.openai.com/plugins/build/plugins)。
