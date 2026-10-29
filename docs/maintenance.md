# 维护指南

[返回首页](../README.md) · [使用手册](usage.md)

本文用于维护仓库源码、第三方快照与开发验证；客户端安装、调用和刷新见使用手册。

本仓库支持 Codex、Claude Code、Antigravity CLI（agy）与 DeepSeek Harness 桌面版（dsh）。项目规则、配置、能力、调用方式、支持范围或维护流程有变化时，同步检查并更新 README 与直接相关文档，维护要求以 [AGENTS.md](../AGENTS.md) 为准。

agy 全局同步使用项目 Skill `.agents/skills/sync-agy/`，Claude 入口只引用共享正文；它从现有产品 catalog 读取目标，通过原生 CLI 校验、安装与验证，不进入 Marketplace 产品清单。已退出 catalog 的插件只有在安装目录及 manifest 确认属于本仓库时才自动停用并移入回收站；预检只报告，不修改。各产品沿用原有 `plugin.json`，第三方上游 Skills 不直接修改。安装与业务执行分开验证，具体用法见[agy 使用说明](usage.md#antigravity-cliagy)。

dsh 桌面同步使用 `.agents/skills/sync-dsh/`；Claude / agy 项目入口只引用共享正文。它从产品 catalog 收集共享 Skills，完整保留资源，使用桌面版自带的 Electron / 文件系统 provider 隔离读取并验证清单与调用策略，再发布内容摘要快照和独立的 provider patch。第三方快照保持原样。当前核验桌面版 `0.2.1-rc.2`，不调用 npm CLI、不修改模型或权限。见[使用手册](usage.md#deepseek-harness-桌面版dsh)。

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
│   ├── matt/                      # 精选 Matt 原始 Skill 完整目录
│   ├── common-workflow/           # 第三方快照
│   ├── software-dev/              # 第三方快照
│   └── engineering-tools/          # 第三方快照
├── docs/
│   ├── usage.md
│   └── maintenance.md
└── README.md                      # 概览与文档入口
```

四个 Plugin 共 26 个 Skills：matt 17、common-workflow 1、software-dev 5、engineering-tools 3。四端产品清单一致；Codex 沿用便携 `plugin.json`，Claude 使用 `.claude-plugin/plugin.json`，两端 Marketplace 指向同一产品根。

Codex 便携 manifest 的中文信息位于 `extensions.com.openai.interface`；Claude manifest / catalog 有意不写 version，Git 来源按 commit 跟踪更新；validator 的缺少 version 警告属于此版本策略。参考 [OpenAI Plugin 规范](https://developers.openai.com/plugins/build/plugins)与 [Claude 版本策略](https://code.claude.com/docs/en/plugins/host-marketplace)。

## 第三方来源与维护边界

[sources.yaml](../sources.yaml) 是第三方来源的唯一人工维护入口，记录 group / displayName 及各 Skill 的 name、repo、path、ref。新增、移除、换源、路径、分组或 ref 先改该文件，再同步；作者与 upstream 只表示来源，不决定分类。`sync.py` 会在 fetch 或发布前拒绝来源 YAML 与 lock JSON 中的重复映射键，同时保留合法 YAML merge 覆盖。

准确 repo / path / ref 查看配置，实际完整 commit 查看 [sources.lock.json](../sources.lock.json)。当前 Anthropic 与 antfu 来源固定在 commit，FastAPI 跟随 master，其余配置跟随 main；分支同步到当前内容，固定 commit 保持固定，改变固定版本需明确修改 ref。

lock 自动记录来源、分类、实际同步 commit 与 UTC 同步时间，不参与版本选择，不手工维护。

当前来源包含四个分类、26 个第三方 Skill；matt 只登记明确选择的 17 项，repo 为 mattpocock/skills、ref 为 main、path 使用上游实际目录。sources 是选择清单，不扫描或镜像整个 stable 目录。推荐主链与完整名单见[使用手册](usage.md#matt-精选工作流)。

`software-dev` 收录第三方上游项目的 Skills，仅由本仓库汇集、整理供个人使用；作者署名、上游内容及许可证均按原样保留。

第三方 `skills/` 原样同步，不手工修改快照；[.gitattributes](../.gitattributes) 禁止 Git 转换这些文件的换行。Skill 内许可证保留原样，upstream 根 LICENSE / NOTICE 等另存到 `licenses/<skill-name>/`。快照随仓库发布，换电脑通过 Plugin 安装恢复。

项目 `upgrade` Skill 和各 manifest 直接维护，不进入 sources / lock。新增第三方 Skill 优先归入现有分类；Matt 子集只通过明确选择扩展；只有新的领域才考虑增加分类。自有 Plugin 不走第三方同步。第三方 `resolving-merge-conflicts`、standalone `pdf` 和 Legacy 入口不保留。

`playwright-cli` 的来源、固定快照、许可证、正文与触发策略保持不变，仅分组迁入 `engineering-tools`。同步白名单与两端 marketplace 使用新分组；agy / dsh 继续由 catalog 发现产品，不增加独立适配层。旧安装与调用前缀的迁移见[使用手册](usage.md#安装与更新)。

### 同步工具写入边界

`scripts/sync.py` 的 `MANAGED_PLUGINS` 只允许 common-workflow、matt、software-dev、engineering-tools 四个第三方分类。新增 sources 分组不能授予其他目录写入权限；未知分组、混入非 Generated 项的 lock、Owned 目标、manifest 目标或重定向目录均在写入前拒绝。

发布与回滚只允许写 `plugins/<managed>/skills/<name>`、`plugins/<managed>/licenses/<name>` 和根 lock。脚本不遍历 Owned 目录清理，新建自有 Plugin 不修改该白名单。

## 升级第三方 Skill

### 使用项目 Skill

在本仓库 Codex 聊天调用 `$upgrade`，共享正文为 [.agents/skills/upgrade/SKILL.md](../.agents/skills/upgrade/SKILL.md)；Claude Code 调用 `/upgrade`，发现入口为 [.claude/skills/upgrade/SKILL.md](../.claude/skills/upgrade/SKILL.md)，再读取共享正文。它不计入 Codex / Claude Code Marketplace 的 26 个 Skills。

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

所有来源拉取与校验通过后才替换本地快照；普通写入失败会恢复替换前的快照与 lock。回滚再次失败时继续尝试其他项目的恢复，报告未恢复项并保留备份。每次运行的 `.agent-tmp/sync/<run-id>/` 由脚本输出并保留，失败或中断不清理；验证、整体检查及已授权收尾完成后，按项目清理规则处理本次目录。网络、ref 或 path 失败时非零退出，保留原有内容。相同 commit 且内容未变时保留同步时间；重复运行不制造 lock 差异，也能恢复误改或缺失的快照。

单个快照同步时会移除 upstream 已删除的文件；整项从配置移除时，旧 Skill 和记录会保留并提示人工检查。脚本不自动推荐、分类或更换 upstream；仓库没有后台更新、semver 解析或 GitHub Actions 自动更新。

同步后检查：

```powershell
git status --short
git diff --stat
git diff -- sources.lock.json
git diff --check
```

首次生成的文件为 untracked，结合 status 核对。回退 upstream 内容时，将 ref 改为 lock 中记录的目标 commit，再运行同步。

## 开发验证

以下命令用于开发验收，按改动范围选择。执行 Python 前按上方核对 mise 和实际版本；执行 Node 前同样核对项目约束、`mise current` 与 `node -v`。文档整理无需运行这些客户端或模型流程。

项目内测试 fixture 和进程临时文件使用 `.agent-tmp/tests/<run-id>/`；TMP / TEMP 仅在该测试进程指向本次运行目录，不修改系统或用户环境。

### Manifest 检查

Claude Marketplace 与分类 manifest 可用原生验证器检查，例如：

```powershell
claude plugin validate .
claude plugin validate plugins/software-dev
```

其他分类同理；缺少 version 的警告按上方版本策略判断。

### 常规测试

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -v
```

真实客户端测试默认不启用。仅同步改动可缩小为：

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -p test_sync.py -v
```

| 测试入口 | 覆盖内容 |
| --- | --- |
| `tests/test_sync.py` | 重复同步、快照恢复、upstream 更新、许可证、失败不写入、路径与重名拒绝、回滚和移出配置项保留 |
| `tests/test_agy_sync.py` | 模拟 agy CLI 检查只读预检、产品同步、禁用状态保留、资源核对与失败停止；不修改真实 agy 配置 |

### Codex 隔离加载器

`tests/test_codex_loader.py` 验证保留产品的发现与显式调用。显式启用后运行常规测试命令：

```powershell
$env:MARKETPLACE_CODEX_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -v
Remove-Item Env:MARKETPLACE_CODEX_TESTS
```

使用项目内隔离 CODEX_HOME、临时项目、安装 fixture 与 localhost 请求捕获器，不调用真实模型、不执行 Skill 正文，也不更新日常全局配置或安装缓存。

`tests/test_matt.py` 检查精选清单、运行依赖、内部资源、来源与 manifest 一致性；目录字节完整性还需与本次实际 fetch 的 upstream commit 核对。
该加载用例已在 Codex CLI 0.160.1 与 0.162.0-alpha.17.2 上通过；这是实际验证版本记录，不定义版本支持范围。隔离 fixture 显式让 localhost 绕过代理，并关闭远端 Plugin 同步和系统代理回退，避免工作站网络配置干扰加载证据；失败时保留 fixture 内的退出诊断。

2026-10-12 目录调整实测：Codex CLI `0.162.0-alpha.17.2` 可发现并显式加载新增的 `java-springboot` 与 `docker-compose-patterns`；Java 正文完整注入，Compose 的 `SKILL.md` 为 9739 字节，当前 CLI 仅直接注入前 8000 字节。随包文件完整保留，使用时仍需按需读取完整入口与引用资源；加载测试通过不代表长正文完整注入。

### Claude 隔离加载器

`tests/test_claude_loader.py` 覆盖四个 Plugin 安装与发现、手动策略、项目 upgrade 入口及 CLAUDE.md 导入 AGENTS.md：

```powershell
$env:MARKETPLACE_CLAUDE_TESTS = "1"
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -v
Remove-Item Env:MARKETPLACE_CLAUDE_TESTS
```

使用独立 CLAUDE_CONFIG_DIR、临时 Git 项目与 localhost 捕获请求后拒绝推理，不运行真实模型或修改日常配置。

2026-10-28 Playwright 合并针对性验证：包装、来源同步、agy 模拟同步、dsh 同步及真实 provider共 **72 项通过**；Codex CLI `0.165.0-alpha.1.2` 与 Claude Code `2.1.307` 的安装 / 发现 / 显式加载另各 1 项通过。agy `1.4.5` 原生校验识别 `engineering-tools` 的 3 个 Skills，未执行日常全局安装。dsh 使用 `0.2.1-rc.2`。Playwright 的正文、引用与许可证共 12 个文件迁移前后字节一致，来源 commit / ref / 时间保留；Codex 仍只直接注入长入口的前 8000 字节，完整文件与引用资源须按需读取。Claude 安装 / 加载测试独立于配置编辑器的精确版本前置检查，未扩大编辑器的已验证版本集合。以上不代表真实模型、浏览器业务流程或当前桌面会话已验收。

### 历史验收范围

以下是原 README 中 2026-10-10 的工程验收记录，本次文档整理没有重新运行这些测试。

| 客户端 | 当时版本 | 已记录的验证 |
| --- | --- | --- |
| Codex | `0.162.0-alpha.2` | 四个第三方 Plugin / 13 个 Skills 的安装、发现、字节与 metadata 核对及旧入口清理 |
| Claude Code | `2.1.296` | 隔离安装五个 Plugin、发现 16 个 Skills、手动策略与项目配置覆盖 |

这些工程检查覆盖包装、发现、内容与配置能力，未逐个执行全部 Skill 的业务流程。日常安装成功与隔离工程验收分别记录，不能由前者推断所有 Skill 内部流程都已验证。

## 交付

修改后核对实际 diff、无关改动与文档一致性，按风险执行必要验证，并运行 `git diff --check`。影响用户使用时更新使用手册；影响概览或入口时更新 README。

按 [AGENTS.md](../AGENTS.md) 默认在同一收尾流程提交并推送当前分支，遵循 Conventional Commits；先推送 Gitee `origin`，成功后再推送 GitHub `github` 的同名分支。GitHub 失败不回滚 Gitee、不阻塞任务完成，分别报告两端结果。
