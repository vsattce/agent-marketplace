# agent-marketplace

个人使用的 Skill / Plugin 集合，Codex 中显示为 **Agent Marketplace**。按用途固定为四个 Plugin，共 13 个已选定的 Skills。作者、GitHub 仓库和 upstream 只作为来源信息，不决定分类。

当前先完成 Codex。Skill 内容作为共享核心，其他 Agent 的 manifest / adapter 后续单独增加；本轮没有实现 Claude Code、Kimi Code 或 Antigravity 适配。

## 四个 Plugin

| Plugin 标识 | 中文名称与简介 | Skills |
| --- | --- | --- |
| `common-workflow@agent-marketplace` | **通用工作流**：任务交接、问题诊断、资料研究与 Agent 工作流工具。 | handoff、diagnosing-bugs、research、writing-for-agents、find-skills |
| `frontend-dev@agent-marketplace` | **前端开发**：前端界面设计、Vue 开发与 Web 设计规范。 | frontend-design、web-design-guidelines、vue、vue-best-practices |
| `backend-dev@agent-marketplace` | **后端开发**：Java / Spring Boot 开发与工程实践。 | java-spring-boot |
| `testing-automation@agent-marketplace` | **测试与自动化**：网页测试、Playwright 浏览器自动化与测试最佳实践。 | webapp-testing、playwright-cli、playwright-best-practices |

默认继续使用已选定的 Skill 和来源；新增 Skill 优先归入四类，只有新的领域才考虑增加分类。`resolving-merge-conflicts` 和第三方 standalone `pdf` 不保留，也没有 Legacy 入口。

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
│   └── testing-automation/
└── README.md
```

每个 Plugin 包含根目录 `plugin.json`、`skills/<skill-name>/` 和 `licenses/<skill-name>/`。Plugin 根使用便携 manifest，中文信息位于 `extensions.com.openai.interface`；Marketplace 的 `skills: "./skills/"` 与原生目录发现指向同一组共享内容。

`sources.yaml` 是来源的主要维护入口，只记录 group / displayName 及各 Skill 的 `name`、`repo`、`path`、`ref`。修改来源或 ref 时只编辑该文件。`sources.lock.json` 自动记录来源、分类、实际同步 commit 和 UTC 同步时间，不参与版本选择。

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

## Codex 添加、安装与刷新

Marketplace 使用原生本地目录 source，四个入口指向 `./plugins/<group>`，路径相对于 Marketplace 仓库根。GitHub 来源也从市场快照的相对目录安装，不再逐张卡片下载 upstream。

换电脑恢复时，从已经发布的 GitHub 仓库安装：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add frontend-dev@agent-marketplace --json
codex plugin add backend-dev@agent-marketplace --json
codex plugin add testing-automation@agent-marketplace --json
```

本地开发使用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。同名 Marketplace 切换来源时，先用 `codex plugin marketplace list` 核对，再移除旧注册并添加目标来源。用 `codex plugin list --marketplace agent-marketplace --available --json` 查看入口。

安装后默认启用，可在 UI 单独 Enable / Disable 整个分类。新建聊天加载迁移后的名称；界面未刷新时重开客户端。调用标识例如 `$common-workflow:handoff`、`$frontend-dev:vue`、`$testing-automation:playwright-cli`。保持 upstream 策略：handoff 仅手动，其余按任务匹配，也可显式调用；启用不会自动执行。

同步只更新仓库，Codex 从安装缓存加载。本地同步后重复执行对应 `codex plugin add <group>@agent-marketplace --json` 刷新安装副本；GitHub 来源先刷新 Marketplace 再重新安装对应 Plugin。Plugin 不安装 Playwright / Java / Vue 运行依赖，使用时遵循目标项目环境约束。

## 本机验证与清理

2026-10-10，使用 `codex-cli 0.162.0-alpha.2` 在日常配置安装并启用四个 Plugin。仓库外新进程的 `skills/list` 发现 5 / 4 / 1 / 3 个指定 Skills，全部文件与仓库快照字节一致，中文 metadata 正确。新 Plugin 验证成功后，已用 Codex 原生命令卸载旧八个细粒度 Plugin，再次发现恰好 13 个目标 Skills，没有重复加载。

本轮开始时，以下 standalone 已不存在，完成后再次确认均不存在：`diagnosing-bugs`、`handoff`、`research`、`writing-for-agents`、`frontend-design`、`webapp-testing`、`vue`、`vue-best-practices`、`find-skills`、`web-design-guidelines`、`java-spring-boot`、`playwright`、`playwright-best-practices`、`resolving-merge-conflicts`、`pdf`。`~/.codex/skills` 仅剩 `.system`，非系统目录为零；系统 Skills 和其他市场未改动。

旧 `plugins/marketplace-smoke/` 只有空测试目录，无文件、manifest 或 Skill，不在 Git 或 Marketplace 中。自动审批检查拒绝了其递归和空目录删除，只返回 `blocked by policy`，因此空目录仍保留，不影响四个 Plugin。

以上验证覆盖安装、启用、metadata、发现和文件来源，没有逐个执行全部 Skill 内部开发流程，也没有用桌面截图验收卡片渲染。当前聊天的 Skill 列表是开始时注入的旧快照，迁移后的名称在新聊天加载。

同步工具测试：

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -m unittest discover -s tests -v
```

覆盖重复同步、快照恢复、upstream 内容更新、许可证保留、网络 / 目录失败不写入、非法路径与重名拒绝、替换失败恢复，以及不自动删除移出配置的 Skill。

本轮不自动 commit / push；发布前 GitHub 来源仍为旧结构，本机新结构使用本地工作区来源。

加载方式参考 [OpenAI Plugin 规范](https://developers.openai.com/plugins/build/plugins)。
