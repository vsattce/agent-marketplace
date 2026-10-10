# 维护指南

[返回首页](../README.md) · [使用手册](usage.md)

本文用于维护仓库源码、第三方快照与开发验证；客户端安装、调用和刷新见使用手册。

## 目录与职责

```text
agent-marketplace/
├── .agents/
│   ├── plugins/marketplace.json    # Codex Marketplace
│   └── skills/upgrade/SKILL.md     # 项目升级入口
├── .claude-plugin/marketplace.json # Claude Marketplace
├── kimi.plugin.json               # Kimi 整仓库聚合入口
├── AGENTS.md                      # 项目规则
├── CLAUDE.md                      # 导入 AGENTS.md
├── sources.yaml                   # 第三方来源配置
├── sources.lock.json              # 已同步 commit 与时间
├── scripts/sync.py                # 第三方同步工具
├── tests/                         # 同步、管理工具与客户端验收
├── plugins/
│   ├── common-workflow/           # 第三方快照
│   ├── frontend-dev/              # 第三方快照
│   ├── backend-dev/               # 第三方快照
│   ├── testing-automation/        # 第三方快照
│   ├── agent-manager/             # OWNED，直接维护
│   └── personal-dev/              # OWNED，Codex 专用、仅手动
├── docs/
│   ├── usage.md
│   └── maintenance.md
└── README.md                      # 概览与文档入口
```

原五个跨客户端分类共享 `skills/<name>/`，提供 Codex `plugin.json`、Claude `.claude-plugin/plugin.json` 与 Kimi `kimi.plugin.json`。第三方分类另存 `licenses/<name>/`。Codex / Claude Marketplace 均指向 `./plugins/<plugin>`；Kimi 根 manifest 列出五个共享 Skill 目录。`personal-dev` 仅在 Codex 注册，包含两个仅手动调用的 Skill，不加入 Claude / Kimi catalog。

Codex 使用便携 manifest，中文信息位于 `extensions.com.openai.interface`。Claude manifest / catalog 有意不写 version，GitHub 来源按 commit 跟踪更新；validator 的缺少 version 警告属于此版本策略。Kimi 的 version 是显示 metadata，判断 GitHub 内容需比较 receipt 的 ref / installedSha。参考 [OpenAI Plugin 规范](https://developers.openai.com/plugins/build/plugins)与 [Claude 版本策略](https://code.claude.com/docs/en/plugins/host-marketplace)。

## 第三方来源与维护边界

[sources.yaml](../sources.yaml) 是第三方来源的唯一人工维护入口，记录 group / displayName 及各 Skill 的 name、repo、path、ref。新增、移除、换源、路径、分组或 ref 先改该文件，再同步；作者与 upstream 只表示来源，不决定分类。

准确 repo / path / ref 查看配置，实际完整 commit 查看 [sources.lock.json](../sources.lock.json)。当前 Anthropic 与 Vue 来源固定在 commit，其余配置跟随 main；分支同步到当前内容，固定 commit 保持固定，改变固定版本需明确修改 ref。

lock 自动记录来源、分类、实际同步 commit 与 UTC 同步时间，不参与版本选择，不手工维护。

第三方 `skills/` 原样同步，不手工修改快照；[.gitattributes](../.gitattributes) 禁止 Git 转换这些文件的换行。Skill 内许可证保留原样，upstream 根 LICENSE / NOTICE 等另存到 `licenses/<skill-name>/`。快照随仓库发布，换电脑通过 Plugin 安装恢复。

`agent-manager`、`personal-dev`、项目 `upgrade` Skill 和各 manifest 直接维护，不进入 sources / lock。新增第三方 Skill 优先归入现有四类；只有新的领域才考虑增加分类。自有 Plugin 不走第三方同步。第三方 `resolving-merge-conflicts`、standalone `pdf` 和 Legacy 入口不保留。

### 同步工具写入边界

`scripts/sync.py` 的 `MANAGED_PLUGINS` 只允许四个第三方分类。新增 sources 分组不能授予其他目录写入权限；未知分组、混入非 Generated 项的 lock、Owned 目标、manifest 目标或重定向目录均在写入前拒绝。

发布与回滚只允许写 `plugins/<managed>/skills/<name>`、`plugins/<managed>/licenses/<name>` 和根 lock。脚本不遍历 Owned 目录清理，新建自有 Plugin 不修改该白名单。

## 升级第三方 Skill

### 使用项目 Skill

在本仓库 Codex 聊天调用 `$upgrade`，入口为 [.agents/skills/upgrade/SKILL.md](../.agents/skills/upgrade/SKILL.md)。它不计入 Codex 六个 Plugin 的 18 个 Skills，也不计入 Claude / Kimi 五个 Plugin 的 16 个 Skills。

Agent 核对目标、Git 状态与运行时后，按 sources 的既定来源 / ref 同步，保留用户改动，检查差异并运行相关验证。按 [AGENTS.md](../AGENTS.md) 默认提交、推送当前分支；当前任务明确不提交或不推送时遵从该要求。环境、同步或验证失败时停止，零差异不制造提交。

项目 Skill 从 `.agents/skills/` 发现；当前聊天未显示 `$upgrade` 时，新建本项目聊天，仍未出现再重启 Codex。此入口升级仓库快照，客户端安装副本按[使用手册](usage.md#安装与更新)另行刷新。

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

源码在 [plugins/agent-manager](../plugins/agent-manager)，三个 Skill 均仅手动调用。用户行为与支持范围见[使用手册](usage.md#agent-管理工具)，这里保留维护入口：

| 内容 | 入口 |
| --- | --- |
| 冲突查找工作流 | [resolve-conflicts](../plugins/agent-manager/skills/resolve-conflicts/SKILL.md) |
| 只读版本比较与共享 API helper | [check-updates](../plugins/agent-manager/skills/check-updates/SKILL.md) |
| 项目指令、Skill 安装、开关工作流与编辑器 | [configure-project](../plugins/agent-manager/skills/configure-project/SKILL.md) |
| Codex / Claude / Kimi 来源与加载机制 | [Codex](../plugins/agent-manager/references/codex.md)、[Claude](../plugins/agent-manager/references/claude.md)、[Kimi](../plugins/agent-manager/references/kimi.md) |
| 其他 Agent 的只读来源发现 | [agent-sources.md](../plugins/agent-manager/references/agent-sources.md) |
| 项目文件预检、开关能力与输入契约 | [project-edits.md](../plugins/agent-manager/skills/configure-project/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/configure-project/references/codex-support.md)、[Claude](../plugins/agent-manager/skills/configure-project/references/claude-support.md)、[editor-input.md](../plugins/agent-manager/skills/configure-project/references/editor-input.md) |

Plugin 开关编辑器的 Codex 分支使用 tomlkit 0.13.3+（<1）保留注释与排版；Claude 分支使用标准库增量替换 JSON 值，拒绝重复键和损坏配置。它只处理 Plugin 开关；AGENTS.md 与 standalone Skill 文件操作由 Skill 层完成，并在混合请求写入前统一预检。现有开关事务保留无关字节，具备幂等、锁、原子替换、二次读取和失败恢复；Windows 路径、symlink、junction 与 hardlink 的拒绝行为有测试覆盖。

Skill 运行时使用已准备的 Agent 工具环境，不安装依赖、不启动客户端做能力探测，不用全局写入弥补项目能力缺失。客户端版本适配先补充真实隔离证据，再更新编辑器的已验证版本常量及支持说明。Gemini 来源发现说明不代表其 Marketplace 安装已适配。

## 开发验证

以下命令用于开发验收，按改动范围选择。执行 Python 前按上方核对 mise 和实际版本；执行 Node 前同样核对项目约束、`mise current` 与 `node -v`。文档整理无需运行这些客户端或模型流程。

### Manifest 检查

Claude Marketplace 与分类 manifest 可用原生验证器检查，例如：

```powershell
claude plugin validate .
claude plugin validate plugins/frontend-dev
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
| `tests/test_agent_manager.py` | Plugin 包装、手动策略、Kimi manifest 与只读来源比较 |
| `tests/test_personal_dev.py` / `tests/test_personal_dev_review.py` / `tests/test_personal_dev_packaging.py` | 开发与审查模型选择、阻塞与安全 CLI 输出，以及 Codex 专用包装和手动策略 |
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

`tests/test_personal_dev_loader.py` 复用同一隔离方式，检查新 Plugin 的发现、普通提示不注入以及显式调用注入。模型选择检查器与 Skill 流程独立维护，当前系列识别不代表已经验证任意未来命名或实际额度折算。
该加载用例已在 Codex CLI 0.160.1 上通过；这是实际验证版本记录，不定义版本支持范围。

### Claude 隔离加载器

`tests/test_claude_loader.py` 覆盖五个 Plugin 安装与发现、手动策略、项目值覆盖用户值及 local 反向覆盖：

```powershell
$env:AGENT_MANAGER_CLAUDE_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
Remove-Item Env:AGENT_MANAGER_CLAUDE_TESTS
```

使用独立 CLAUDE_CONFIG_DIR、临时 Git 项目与 localhost 捕获请求后拒绝推理，不运行真实模型或修改日常配置。

### Kimi 核心函数

`tests/kimi_loader.cjs` 使用已安装 Kimi Desktop 的 ASAR；路径以本机实际安装为准。历史验收使用 mise Node 24.19.0、Kimi Desktop 1.0.4：

```powershell
mise current
node -v
$env:KIMI_CODE_TEST_ASAR = "D:/Kimi Code/resources/app.asar"
node --test tests/kimi_loader.cjs
Remove-Item Env:KIMI_CODE_TEST_ASAR
```

未设置 ASAR 环境变量时跳过。测试只执行指定核心函数，不启动 Electron、不读取日常 Kimi 数据或联网推理。默认离线；额外设置 `$env:KIMI_CODE_TEST_GITHUB = "1"` 可验证已发布仓库的原生 GitHub 下载、解压与安装，需要网络可达，完成后移除该变量。代理仅使用该进程已配置的代理，不改系统设置。

### 历史验收范围

以下是原 README 中 2026-10-10 的工程验收记录，本次文档整理没有重新运行这些测试。

| 客户端 | 当时版本 | 已记录的验证 |
| --- | --- | --- |
| Codex | `0.162.0-alpha.2` | 四个第三方 Plugin / 13 个 Skills 的安装、发现、字节与 metadata 核对及旧入口清理；管理工具的加载与项目配置能力另有隔离测试 |
| Claude Code | `2.1.296` | 隔离安装五个 Plugin、发现 16 个 Skills、手动策略与项目配置覆盖 |
| Kimi Code Desktop | `1.0.4` | 原生核心函数验证整仓库与五分类安装、16 项发现、资源复制、receipt、手动策略及启停 |

这些工程检查覆盖包装、发现、内容与配置能力，未逐个执行全部 Skill 的业务流程。日常安装成功与隔离工程验收分别记录，不能由前者推断所有 Skill 内部流程都已验证。

## 交付

修改后核对实际 diff、无关改动与文档一致性，按风险执行必要验证，并运行 `git diff --check`。影响用户使用时更新使用手册；影响概览或入口时更新 README。

按 [AGENTS.md](../AGENTS.md) 默认在同一收尾流程提交并推送当前分支，遵循 Conventional Commits，以远端收到提交为完成条件；推送失败如实报告。管理 Skill 在用户项目内执行时不 commit / push。
