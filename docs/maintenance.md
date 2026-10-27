# 维护指南

[返回首页](../README.md) · [使用手册](usage.md)

本文用于维护仓库源码、第三方快照与开发验证；客户端安装、调用和刷新见使用手册。

本仓库支持 Codex、Claude Code、Antigravity CLI（agy）与 DeepSeek Harness 桌面版（dsh）。项目规则、配置、能力、调用方式、支持范围或维护流程有变化时，同步检查并更新 README 与直接相关文档，维护要求以 [AGENTS.md](../AGENTS.md) 为准。

agy 全局同步使用项目 Skill `.agents/skills/sync-agy/`，Claude 入口只引用共享正文；它从现有产品 catalog 读取目标，通过原生 CLI 校验、安装与验证，不进入 Marketplace 产品清单。各产品沿用原有 `plugin.json`；`agent-manager` 使用独立 `.antigravity-plugin/plugin.json`，保留 Codex 专用 `codex-skills/` 的发现边界。自有插件的 agy 行为只维护在随包 `references/agy.md` 及必要入口分支，第三方上游 Skills 不直接修改。安装与业务执行分开验证，具体用法见[agy 使用说明](usage.md#antigravity-cliagy)。

dsh 桌面同步使用 `.agents/skills/sync-dsh/`；Claude / agy 项目入口只引用共享正文。它从产品 catalog 收集共享 Skills，完整保留资源，使用桌面版自带的 Electron / 文件系统 provider 隔离读取并验证清单与调用策略，再发布内容摘要快照和独立的 provider patch。第三方快照保持原样；自有行为维护在必要入口分支与 `references/dsh.md`。当前核验桌面版 `0.2.1-rc.2`，不调用 npm CLI、不修改模型或权限。见[使用手册](usage.md#deepseek-harness-桌面版dsh)。

同步回归使用 `test_dsh_sync.py`，默认模拟用户根和桌面调用；显式设置 `DSH_DESKTOP_TESTS` 为真实桌面程序路径，可启用仅本地读取的原生 provider 验证，不启动 Host / LLM、不改变日常用户配置。验证命令沿用下文 unittest 的 mise / uv 环境约束。

## Claude Code plugin 开发指导

`.agents/plugin-dev/upstream/` 保留 Anthropic 官方 `claude-plugins-official/plugins/plugin-dev` 的完整快照，来源 commit、仓库和路径记录在 [.agents/plugin-dev/source.json](../.agents/plugin-dev/source.json)。它随项目分发，独立于 `sources.yaml` / `sources.lock.json`，不注册到 Marketplace。Codex 从工作目录到仓库根目录发现 `.agents/skills/` 项目 Skill，支持显式 `$claude-plugin-dev` 调用并按描述匹配相关任务，加载规则见 [Codex Skills 官方说明](https://learn.chatgpt.com/docs/build-skills)。项目 Skill 按 manifests/discovery、commands、agents、hooks、MCP、settings、Skills 七个主题指向快照中的对应内容；仅按需读取相关指南与资源。

刷新时从官方仓库选择并记录明确 commit，完整替换 `upstream/` 子树并保留上游 LICENSE、文件字节及可执行标记，再更新 `source.json`、Skill 路径引用和测试中的来源 commit、摘要与 mode 基线。此项目 Skill 只为仓库开发提供 Claude Code plugin 指导；不安装 Claude 原生 `plugin-dev` bundle、不把 Claude 专用命令或字段解释为 Codex 能力，也不代表已验证 Claude 客户端加载。版本敏感行为应再核对当前 Claude Code 官方文档。

## 仓库开发工具

仓库开发工具（repository development tooling）包括 .agents/skills/ 中的 Superpowers、项目 upgrade、sync-agy、Claude Code plugin 开发 Skill 与未来项目级开发 Skill，.agents/plugin-dev/ 中的官方参考快照，以及项目 MCP 与 Codex / Claude 开发辅助配置。这些能力服务仓库维护，不进入 Marketplace 产品目录或数量；除明确要求，不注册到 .agents/plugins/marketplace.json、.claude-plugin/marketplace.json、sources.yaml 或对外安装目录。Superpowers 仅在用户明确手动指定时调用，不作为日常维护的默认启动流程，且不计入 Marketplace 数量。第三方快照与 OWNED 内容的维护方式见下文“第三方来源与维护边界”。

Codex 项目配置 .codex/config.toml 提供 OpenAI Docs MCP 和 Context7：OpenAI Docs 用于按需核对 Codex / OpenAI 的 plugin、MCP、Skill 与配置行为；Context7 用于外部库、框架、SDK、CLI 的 API、配置格式和版本差异。稳定的本地修改不必每次查文档；复用已有结果，查询不提交凭据、私有源码或会话内容。连接不可用时，转查对应官方网页。配置格式与加载边界见 [Codex 配置文件官方说明](https://learn.chatgpt.com/docs/config-file/config-basic)及 [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp)。

这份 Codex 配置仅用于受信任项目的 Codex 会话。Claude Code 使用自己的项目 MCP 入口 .mcp.json；不得将 Codex 配置直接套用到 Claude。参见 [Claude Code MCP 官方说明](https://code.claude.com/docs/en/mcp)。根目录 CLAUDE.md 只导入 AGENTS.md。

## 目录与职责

```text
agent-marketplace/
├── .agents/
│   ├── plugins/marketplace.json    # Codex Marketplace
│   ├── skills/
│   │   ├── upgrade/SKILL.md        # 项目升级入口
│   │   ├── sync-agy/              # agy 产品插件全局同步入口
│   │   ├── sync-dsh/              # dsh 桌面版产品 Skills 同步入口
│   │   ├── claude-plugin-dev/      # Claude Code plugin 开发指导
│   │   └── …                      # 项目 Superpowers Skills
│   └── plugin-dev/upstream/        # 官方 plugin-dev 固定快照
├── .claude/skills/                # Claude 的 upgrade / sync-agy / sync-dsh 共享正文入口
├── .claude-plugin/marketplace.json # Claude Marketplace
├── AGENTS.md                      # 项目规则
├── CLAUDE.md                      # 导入 AGENTS.md
├── sources.yaml                   # 第三方来源配置
├── sources.lock.json              # 已同步 commit 与时间
├── scripts/sync.py                # 第三方同步工具
├── tests/                         # 同步、管理工具与客户端验收
├── plugins/
│   ├── common-workflow/           # 第三方快照
│   ├── software-dev/              # 第三方快照
│   ├── engineering-tools/          # 第三方快照
│   ├── testing-automation/        # 第三方快照
│   ├── agent-manager/             # OWNED，直接维护
│   └── personal-dev/              # OWNED，Codex / Claude / agy / dsh、仅手动
├── docs/
│   ├── usage.md
│   └── maintenance.md
└── README.md                      # 概览与文档入口
```

六个 Plugin 都提供 Claude Code `.claude-plugin/plugin.json`；Codex 侧除 `agent-manager` 外使用便携 `plugin.json`，该 Plugin 使用原生 `.codex-plugin/plugin.json` 并显式发现 `skills/` 与 `codex-skills/`。`am-context` 放在后者，因此仅 Codex 可发现；`am-config` 仍共享。四个第三方分类另存 `licenses/<name>/`，两个 Marketplace 均指向 `./plugins/<plugin>`。当前 Codex 有 28 个 Skills、Claude Code / agy / dsh 各有 27 个：第三方四类共 20 个，`agent-manager` 分别有 2 / 1 / 1 / 1 个，`personal-dev` 四端各有 6 个。`dev-prepare` / `dev-auto` 复用 `references/preparation.md`；`dev-auto` 直接读取 `dev-delegate` 正文，执行端按 Harness 使用 `references/codex.md` / `references/claude.md` / `references/agy.md` / `references/dsh.md`，Codex 使用现有模型检查器，不新增 Plugin 或调度系统。

`personal-dev` 当前模型规则见[子代理模型契约](../plugins/personal-dev/references/subagent-models.md)：`dev-review` 只必填 `reviewer=<model>:<effort>`，支持 `reviewer / review / r / check`；`dev-delegate` / `dev-auto` 仍必填 worker + reviewer。额外提供的 worker 也须校验。检查器按当前工具元数据校验显式型号和 effort，不自动选型、不 fallback。

执行默认采用短路径：委派为 `worker → reviewer → 必要修复 → 最终 fresh verification → DONE`，审查为 `reviewer → 主模型核验证据 → 输出报告`。普通任务单 worker 顺序执行，普通审查单 reviewer；修复通过即停止，三轮仅是上限。并行、ledger / 恢复、fresh coder、依赖冻结、严重或争议发现的独立复核及重专项验证均按实际需要启用，Final Reviewer 保留原有高风险触发条件。维护时以当前入口、共享契约、adapter 和脚本为准；`docs/superpowers/` 的既有 SPEC / PLAN 保留为阶段记录，当前用法见[使用手册](usage.md#个人开发工具codex--claude-code--agy--dsh)。

Codex 便携 manifest 的中文信息位于 `extensions.com.openai.interface`；原生 Codex manifest 的中文信息使用根级 `interface`。Claude manifest / catalog 有意不写 version，Git 来源按 commit 跟踪更新；validator 的缺少 version 警告属于此版本策略。参考 [OpenAI Plugin 规范](https://developers.openai.com/plugins/build/plugins)与 [Claude 版本策略](https://code.claude.com/docs/en/plugins/host-marketplace)。

## 第三方来源与维护边界

[sources.yaml](../sources.yaml) 是第三方来源的唯一人工维护入口，记录 group / displayName 及各 Skill 的 name、repo、path、ref。新增、移除、换源、路径、分组或 ref 先改该文件，再同步；作者与 upstream 只表示来源，不决定分类。`sync.py` 会在 fetch 或发布前拒绝来源 YAML 与 lock JSON 中的重复映射键，同时保留合法 YAML merge 覆盖。

准确 repo / path / ref 查看配置，实际完整 commit 查看 [sources.lock.json](../sources.lock.json)。当前 Anthropic 与 antfu 来源固定在 commit，FastAPI 跟随 master，其余配置跟随 main；分支同步到当前内容，固定 commit 保持固定，改变固定版本需明确修改 ref。

lock 自动记录来源、分类、实际同步 commit 与 UTC 同步时间，不参与版本选择，不手工维护。

当前来源包含四个分类、20 个第三方 Skill：`common-workflow` 12 个、`software-dev` 5 个、`engineering-tools` 2 个、`testing-automation` 1 个。`common-workflow` 包含 Matt Pocock 的 `codebase-design`、`tdd`，以及用户主动调用的 `grill-me`、`grill-with-docs`、`improve-codebase-architecture` 和允许依赖被动调用的 `grilling`、`domain-modeling`；Docker Compose 使用 Docker 官方 `docker-compose-patterns`，Java 使用 GitHub `awesome-copilot` 的 `java-springboot`。准确来源、路径与固定策略以 sources 配置为准。

`software-dev` 收录第三方上游项目的 Skills，仅由本仓库汇集、整理供个人使用；作者署名、上游内容及许可证均按原样保留。该说明不适用于 `agent-manager`、`personal-dev` 等本仓库自有 Plugin。

第三方 `skills/` 原样同步，不手工修改快照；[.gitattributes](../.gitattributes) 禁止 Git 转换这些文件的换行。Skill 内许可证保留原样，upstream 根 LICENSE / NOTICE 等另存到 `licenses/<skill-name>/`。快照随仓库发布，换电脑通过 Plugin 安装恢复。

`agent-manager`、`personal-dev`、项目 `upgrade` Skill 和各 manifest 直接维护，不进入 sources / lock。新增第三方 Skill 优先归入现有四类；只有新的领域才考虑增加分类。自有 Plugin 不走第三方同步。第三方 `resolving-merge-conflicts`、standalone `pdf` 和 Legacy 入口不保留。

### 同步工具写入边界

`scripts/sync.py` 的 `MANAGED_PLUGINS` 只允许四个第三方分类。新增 sources 分组不能授予其他目录写入权限；未知分组、混入非 Generated 项的 lock、Owned 目标、manifest 目标或重定向目录均在写入前拒绝。

发布与回滚只允许写 `plugins/<managed>/skills/<name>`、`plugins/<managed>/licenses/<name>` 和根 lock。脚本不遍历 Owned 目录清理，新建自有 Plugin 不修改该白名单。

## 升级第三方 Skill

### 使用项目 Skill

在本仓库 Codex 聊天调用 `$upgrade`，共享正文为 [.agents/skills/upgrade/SKILL.md](../.agents/skills/upgrade/SKILL.md)；Claude Code 调用 `/upgrade`，发现入口为 [.claude/skills/upgrade/SKILL.md](../.claude/skills/upgrade/SKILL.md)，再读取共享正文。它不计入两个客户端 Marketplace 的 27 / 27 个 Skills。

Agent 核对目标、Git 状态与运行时后，按 sources 的既定来源 / ref 同步，保留用户改动，检查差异并运行相关验证。按 [AGENTS.md](../AGENTS.md) 默认提交、推送当前分支；当前任务明确不提交或不推送时遵从该要求。环境、同步或验证失败时停止，零差异不制造提交。

Codex 项目 Skill 从 `.agents/skills/` 发现，Claude 从 `.claude/skills/` 发现；当前聊天未显示 `$upgrade` 时，新建本项目聊天，仍未出现再重启 Codex。此入口升级仓库快照，客户端安装副本按[使用手册](usage.md#安装与更新)另行刷新。

### 手动同步

需要 Git、mise 管理的 Python 3.12+ 和 uv。PyYAML 6.x 在脚本 PEP 723 metadata 中声明，通过 uv 隔离安装。

在仓库根先核对运行时；版本缺失或不匹配时停止，由用户处理，不自行安装或切换：

```powershell
mise current
python --version
mise which python
uv --version
```

核对通过后执行：

```powershell
uv run --python (mise which python) --no-python-downloads --script scripts/sync.py
```

已有符合约束且包含 PyYAML 的 Python 环境时，也可 `python scripts/sync.py`。

同步工具按 repo + ref 拉取快照，校验目录、Skill 名称与描述，保留许可证，更新 lock 并报告文件增删改。它不执行 upstream 脚本，不安装 Plugin、不清理 standalone，也不 commit / push。

所有来源拉取与校验通过后才替换本地快照；普通写入失败会恢复替换前的快照与 lock。网络、ref 或 path 失败时非零退出，保留原有内容。相同 commit 且内容未变时保留同步时间；重复运行不制造 lock 差异，也能恢复误改或缺失的快照。

单个快照同步时会移除 upstream 已删除的文件；整项从配置移除时，旧 Skill 和记录会保留并提示人工检查。脚本不自动推荐、分类或更换 upstream；仓库没有后台更新、semver 解析或 GitHub Actions 自动更新。

同步后检查：

```powershell
git status --short
git diff --stat
git diff -- sources.lock.json
git diff --check
```

首次生成的文件为 untracked，结合 status 核对。回退 upstream 内容时，将 ref 改为 lock 中记录的目标 commit，再运行同步。

## 自有 Agent 管理工具

源码在 [plugins/agent-manager](../plugins/agent-manager)。Codex 有 `am-context` 与 `am-config` 两个手动入口，Claude Code / agy 仅发现 `am-config`；用户行为与支持范围见[使用手册](usage.md#agent-管理工具)，这里保留维护入口：

| 内容 | 入口 |
| --- | --- |
| 当前对话可见上下文的粗略估算（仅 Codex） | [am-context](../plugins/agent-manager/codex-skills/am-context/SKILL.md) |
| 项目编辑、只读检查与开关编辑器 | [am-config](../plugins/agent-manager/skills/am-config/SKILL.md) |
| 冲突识别、检查范围与分级输出 | [conflicts.md](../plugins/agent-manager/skills/am-config/references/conflicts.md) |
| 各客户端来源与加载机制 | [Codex](../plugins/agent-manager/references/codex.md)、[Claude](../plugins/agent-manager/references/claude.md)、[agy](../plugins/agent-manager/references/agy.md) |
| 项目文件预检、开关能力与输入契约 | [project-edits.md](../plugins/agent-manager/skills/am-config/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/am-config/references/codex-support.md)、[Claude](../plugins/agent-manager/skills/am-config/references/claude-support.md)、[editor-input.md](../plugins/agent-manager/skills/am-config/references/editor-input.md) |

自有 Skill 命名规则：`personal-dev` 采用 `dev-{action}`，`agent-manager` 采用 `am-{action}`。`am-config` 保持共享 `skills/` 目录；仅 Codex 的 `am-context` 使用 `codex-skills/`。入口使用完整调用名。

Plugin 开关编辑器仅在 Windows 运行；其他平台在配置读写前返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`，该限制不影响 AGENTS.md 与 standalone Skill 操作。Codex 分支使用 tomlkit 0.13.3+（<1）保留注释与排版；Claude 分支使用标准库增量替换 JSON 值，拒绝重复键和损坏配置。编辑器只处理 Plugin 开关；AGENTS.md 与 standalone Skill 文件操作由 Skill 层完成，并在混合请求写入前统一预检。现有开关事务保留无关字节，具备幂等、锁、原子替换、二次读取和失败恢复；Windows 路径、symlink、junction、hardlink 与非普通目标文件的拒绝行为有测试覆盖。

Skill 运行时使用已准备的 Agent 工具环境，不安装依赖、不启动客户端做能力探测，不用全局写入弥补项目能力缺失。客户端版本适配先补充真实隔离证据，再更新编辑器的精确版本集合及支持说明；inventory 版本必须等于实际客户端版本，不以范围匹配放行未知版本。未适配的 Harness 必须返回 `BLOCKED / UNSUPPORTED AGENT`。

## 开发验证

以下命令用于开发验收，按改动范围选择。执行 Python 前按上方核对 mise 和实际版本；执行 Node 前同样核对项目约束、`mise current` 与 `node -v`。文档整理无需运行这些客户端或模型流程。

Windows 若系统临时目录使用 `ADMINI~1` 等短路径别名，路径安全测试会拒绝该非规范路径。项目内测试 fixture 和进程临时文件使用 `.agent-tmp/tests/<run-id>/`；需要设置 `TMP` / `TEMP` 时，仅在本次测试进程指向该运行目录，不修改系统或用户环境变量。原始测试日志与短期任务证据按需保存在 `.agent-tmp/tasks/<task-id>/`。

### Manifest 检查

Claude Marketplace 与分类 manifest 可用原生验证器检查，例如：

```powershell
claude plugin validate .
claude plugin validate plugins/software-dev
```

其他分类同理；缺少 version 的警告按上方版本策略判断。

### 常规测试

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
```

真实客户端测试默认不启用。仅同步改动可缩小为：

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -p test_sync.py -v
```

| 测试入口 | 覆盖内容 |
| --- | --- |
| `tests/test_sync.py` | 重复同步、快照恢复、upstream 更新、许可证、失败不写入、路径与重名拒绝、回滚和移出配置项保留 |
| `tests/test_agent_manager.py` | Codex / Claude Plugin 包装、手动策略与只读来源比较 |
| `tests/test_agy_sync.py` | 模拟 agy CLI 检查只读预检、产品同步、禁用状态保留、资源核对与失败停止；不修改真实 agy 配置 |
| `tests/test_personal_dev.py` / `tests/test_personal_dev_review.py` / `tests/test_personal_dev_packaging.py` | 开发与审查模型选择、阻塞与安全 CLI 输出，以及六个 Skill 的双端包装、共享资源、加载长度和手动策略 |
| `tests/test_configure_project.py` | Codex 事务编辑、路径安全与不支持能力的拒绝 |
| `tests/test_configure_project_claude.py` | Claude JSON 增量编辑、覆盖检查与失败恢复 |

### Codex 隔离加载器

`tests/test_codex_loader.py` 验证发现与手动调用；`tests/test_project_config_codex.py` 验证项目 Plugin 覆盖、单个 Skill 项目开关未生效及 untrusted 层忽略。显式启用后运行常规测试命令：

```powershell
$env:AGENT_MANAGER_CODEX_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
Remove-Item Env:AGENT_MANAGER_CODEX_TESTS
```

使用项目内隔离 CODEX_HOME、临时项目、安装 fixture 与 localhost 请求捕获器，不调用真实模型、不执行 Skill 正文，也不更新日常全局配置或安装缓存。

`tests/test_personal_dev_loader.py` 复用同一隔离方式，检查六个 Skill 的发现、普通提示不注入新 Skill 正文以及显式调用注入。`tests/fixtures/dev-delegate-scenarios.md` 覆盖准备 / 执行 / 自动模式、默认短路径、按需并行与恢复、一次修复通过、三轮上限、失败隔离和条件终审；推演与静态包装检查不能冒充真实模型 SDD 执行。模型检查器只校验显式参数与传入的当前工具元数据，型号来源和实际派发效果仍由当前会话核验。
该加载用例已在 Codex CLI 0.160.1 与 0.162.0-alpha.17.2 上通过；这是实际验证版本记录，不定义版本支持范围。隔离 fixture 显式让 localhost 绕过代理，并关闭远端 Plugin 同步和系统代理回退，避免工作站网络配置干扰加载证据；失败时保留 fixture 内的退出诊断。

2026-10-12 目录调整实测：Codex CLI `0.162.0-alpha.17.2` 可发现并显式加载新增的 `java-springboot` 与 `docker-compose-patterns`；Java 正文完整注入，Compose 的 `SKILL.md` 为 9739 字节，当前 CLI 仅直接注入前 8000 字节。随包文件完整保留，使用时仍需按需读取完整入口与引用资源；加载测试通过不代表长正文完整注入。

### Claude 隔离加载器

`tests/test_claude_loader.py` 覆盖六个 Plugin 安装与发现、手动策略、六个 personal-dev Skill 显式加载与原生 Agent schema、项目 upgrade 入口、CLAUDE.md 导入 AGENTS.md、项目值覆盖用户值及 local 反向覆盖：

```powershell
$env:AGENT_MANAGER_CLAUDE_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
Remove-Item Env:AGENT_MANAGER_CLAUDE_TESTS
```

使用独立 CLAUDE_CONFIG_DIR、临时 Git 项目与 localhost 捕获请求后拒绝推理，不运行真实模型或修改日常配置。

历史加载记录（涉及已移除的 `dev-yagni`）：2026-10-11 personal-dev 新入口组合实测：Codex CLI `0.162.0-alpha.17.2` 在同一消息中显式调用 `dev-yagni` 与 `dev-simplify`，捕获到两个正文均已注入。Claude Code `2.1.296` 同一消息显式调用两个入口时仅直接注入首个入口；测试断言首个正文已加载，并输出第二个入口是否加载的诊断。组合使用时应分开、先后显式调用。该检查捕获原生上下文后拒绝推理，不代表真实模型行为验收。

此前全量验收记录（非本次目录调整）：主模型在原项目检出亲自运行完整 unittest，启用 `AGENT_MANAGER_CODEX_TESTS=1` 与 `AGENT_MANAGER_CLAUDE_TESTS=1`：**147 项全部通过，无跳过**。运行环境为 mise Python `3.12.13`、uv `0.12.3`；UTF-8、TMP / TEMP 和客户端隔离开关仅设置在本次进程。覆盖六个 Plugin / 20 个 Skills 的包装、personal-dev 四入口加载及项目配置回归，未修改日常客户端配置。原生工作树位于受保护的 `.codex` 路径，项目配置写入测试需在普通项目检出运行，不能放宽路径保护来绕过。

2026-10-12 目录调整针对性验证：同步测试 25 项通过，包装测试 7 项通过、1 项既有失败，Codex / Claude 隔离加载各 2 项通过。既有失败为 `agent-manager` 的 catalog / native manifest 网站地址不同（Gitee / GitHub），已在修改前的提交上复现，本次未改动。Claude Code `2.1.296` 完整加载两项新 Skill；同一消息组合调用 `dev-simplify` 与 `dev-runtime-check` 时仍仅直接注入首个入口，应先后调用。以上加载验证拒绝模型推理，不修改日常客户端配置。

### 历史验收范围

以下是原 README 中 2026-10-10 的工程验收记录，本次文档整理没有重新运行这些测试。

| 客户端 | 当时版本 | 已记录的验证 |
| --- | --- | --- |
| Codex | `0.162.0-alpha.2` | 四个第三方 Plugin / 13 个 Skills 的安装、发现、字节与 metadata 核对及旧入口清理；管理工具的加载与项目配置能力另有隔离测试 |
| Claude Code | `2.1.296` | 隔离安装五个 Plugin、发现 16 个 Skills、手动策略与项目配置覆盖 |

这些工程检查覆盖包装、发现、内容与配置能力，未逐个执行全部 Skill 的业务流程。日常安装成功与隔离工程验收分别记录，不能由前者推断所有 Skill 内部流程都已验证。

### 2026-10-11 自有能力双平台验收

Windows Python 3.12.13，Codex CLI `0.162.0-alpha.17.2`、Claude Code `2.1.291`。同时启用两端隔离测试，以规范项目路径作为本次测试进程的临时目录，完整 Python 测试 **127 项全部通过，无跳过**。

覆盖六个 Plugin / 18 个 Skills 的双端注册包装、管理工具和 personal-dev 的发现与手动加载、Claude 原生 Agent schema、项目 `/upgrade` 入口与 `CLAUDE.md` 导入 `AGENTS.md`、两端项目 Plugin 覆盖及配置事务。保留此前验证版本；新增精确版本仍须与本轮实际客户端版本一致，未知版本继续拒绝。

Claude `2.1.291` 捕获到的 Agent 参数为 `description`、`isolation`、`model`、`prompt`、`run_in_background`、`subagent_type`，没有 `effort`；该记录只代表当时 schema。当前 personal-dev 要求显式 worker / reviewer，两项均须核验，工具无法覆写 effort 时立即中断，不再省略参数继承默认。共享 helper 的参数、模型名单与 effort 支持有单元测试；四端 adapter 统一映射执行型 worker 与判断型 reviewer。未运行真实模型委派或逐项业务流程，不把请求捕获和场景检查称为真实推理验收。

## 交付

修改后核对实际 diff、无关改动与文档一致性，按风险执行必要验证，并运行 `git diff --check`。影响用户使用时更新使用手册；影响概览或入口时更新 README。

按 [AGENTS.md](../AGENTS.md) 默认在同一收尾流程提交并推送当前分支，遵循 Conventional Commits；先推送 Gitee `origin`，成功后再推送 GitHub `github` 的同名分支。GitHub 失败不回滚 Gitee、不阻塞任务完成，分别报告两端结果。管理 Skill 在用户项目内执行时不 commit / push。
