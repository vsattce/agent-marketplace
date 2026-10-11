# FastAPI、工程工具与远程运行诊断实施计划

> **For agentic workers:** 用户显式选择 `personal-dev:dev-delegate` 和 `gpt-6-luna`，覆盖通用执行方式建议。主模型编写 spec / plan；一个干净上下文的 `gpt-6-luna / xhigh` 编码代理完成关联改动，另一个 `gpt-6-luna / max` 独立验收；主模型终审、提交并推送当前分支。已授权文档完成后直接执行，不再次等待批准。子代理不继续派生代理、不 commit / push。每个任务累计最多两轮修复。

**Goal:** 双端交付两个可升级的第三方 Skill 和一个支持 SSH 直接取证的手动运行诊断 Skill。

**Architecture:** 复用 sources / lock / sync 和现有双端 Plugin 形式，新增 engineering-tools 分类；运行诊断为轻量正文和 Codex metadata，不引入运行服务或 SSH 框架。

**Tech Stack:** Python 3.12+、PyYAML 6.x、现有 unittest、Markdown / YAML / JSON、Codex 与 Claude 隔离 loader。

**Spec:** [设计规格](../specs/2026-10-11-runtime-and-engineering-skills-design.md)

## Global Constraints

- fastapi → backend-dev；docker-build-strategies → engineering-tools；dev-runtime-check → personal-dev。
- 第三方原样同步、完整资源与许可证；sources 分别跟随官方 master / main，lock 记录准确 commit。
- 保留原有 13 项来源、快照与 lock；只将 engineering-tools 加入 managed 白名单，不放宽其他目标保护。
- Codex / Claude 共用内容；第三方自动匹配 / 手动，运行诊断仅手动。最终 7 Plugin / 23 Skills。
- 用户明确 SSH 目标后直接检查，默认当前模型执行；修复依当次明确要求处理，不额外堆审批，不绕过工具权限，不记录凭据。
- Python 由当前 mise 环境管理，uv 隔离依赖；不安装 / 切换运行时、不修改用户配置。测试进程设置 UTF-8、规范 TMP / TEMP 与禁用 pycache。
- 当前 main 工作区无 tracked / staged / untracked 改动。沿用该检出与当前分支，不额外创建工作树；保留忽略缓存。

## Review Focus

- 新分类不仅注册，还要能在下一次正常 upgrade 同步与更新，且 Owned 目录仍拒绝写入。
- 两个新第三方目录需要完整引用资源与许可证，并保持原始字节和原有快照不变。
- Claude 与 Codex 的新入口均实际发现；手动诊断普通提示不注入，显式提示能加载。
- SSH 诊断以目标主机证据为准，已有授权后不重复确认；连接失败不转查工作站。
- 用户仅诊断与明确要求修复的执行范围不同；量化结果需要时间、单位和有效采样。

## Task 1：一次交付三入口与升级链路

此任务包含共享 catalog、数量断言和 loader 调用点，采用一个编码代理统一修改，避免多写入代理交叉改动。

**Files:**
- Modify: `sources.yaml`、`sources.lock.json`、`scripts/sync.py`、`.gitattributes`
- Create: `plugins/engineering-tools/plugin.json`、`plugins/engineering-tools/.claude-plugin/plugin.json`
- Create: `plugins/backend-dev/skills/fastapi/**`、`plugins/backend-dev/licenses/fastapi/**`
- Create: `plugins/engineering-tools/skills/docker-build-strategies/**`、`plugins/engineering-tools/licenses/docker-build-strategies/**`
- Create: `plugins/personal-dev/skills/dev-runtime-check/SKILL.md`、`plugins/personal-dev/skills/dev-runtime-check/agents/openai.yaml`
- Modify: 两端 Marketplace、backend-dev 与 personal-dev manifests
- Modify: `README.md`、`docs/usage.md`、`docs/maintenance.md`（仅当前说明及必要示例）
- Test: `tests/test_sync.py`、`tests/test_agent_manager.py`、`tests/test_personal_dev_packaging.py`、`tests/test_codex_loader.py`、`tests/test_personal_dev_loader.py`、`tests/test_claude_loader.py`；必要时新增一个直接相关的小测试文件。

**Interfaces:**
- Consumes: 现有 `read_sources(root)`、`sync(root)`、`fetch(source, destination)`、`MANAGED_PLUGINS`、check_sources helper 和两端 loader fixture；保留函数签名与 CLI。
- Produces: 7 Plugin / 23 Skills，sources / lock 15 项，三条准确调用入口，更新后的发现与手动策略回归。

- [x] 先添加 / 更新有意义的测试；记录现有缓存和旧英文断言造成的基线问题。初始新增用例 RED 原输出未保留，不作为可复用证据；最终 GREEN 和独立复验见验证记录。
- [x] 仿照既有 manifest 添加 engineering-tools，更新 managed 白名单与 gitattributes；加入两条准确官方来源。
- [x] 通过既有同步逻辑导入两个完整快照。整仓 FastAPI fetch 超时后，一次性复用旧 lock / 快照并稀疏拉取新增内容，再交给原 sync 发布；旧来源与文件字节未变，不持久增加同步选择器或导入脚本。
- [x] 编写轻量运行诊断正文与中文 metadata，按 spec 覆盖 SSH 直接执行、目标取证、有限采样、判断依据、修复意图和双 Harness 原生工具适配。
- [x] 更新双端 catalog / manifests、版本、中文展示与当前文档；保留历史验收记录语境。
- [x] 运行直接测试，再开启两端隔离 fixture 完整验证；151 项通过，检查第三方资源和许可证、手动策略、数量与同步更新 / 回滚，明确记录 Codex 长正文注入限制。
- [x] 编码代理返回实际差异、验证命令 / 输出、未验证项和轻量场景证据；不提交、不推送。

## Task 2：独立验收与主模型收尾

**Files:** 只读检查 Task 1 全部改动；主模型维护本计划状态与 `docs/superpowers/reviews/2026-10-11-runtime-and-engineering-skills-validation.md`。

**Interfaces:** 消费 spec、实际 staged / unstaged / untracked diff、编码报告和测试证据，返回需求 / 正确性 PASS、FAIL 或 UNVERIFIED，以及带位置与触发条件的阻塞项。

- [x] 独立 `gpt-6-luna / max` 核实所有需求、源快照、升级与双端发现。用最少场景检查诊断行为，不连接未授权服务器、不使用真实凭据、不继续派生。
- [x] `followup_task` 原编码代理完成 1 / 2 轮修复及定向复验；证据充分的检查直接复用。
- [x] 主模型完整检查累计差异和跨入口联动，核对任务文件、凭据、垃圾文件与 `git diff --check`；复用已通过测试。临时缓存清理被自动审批拒绝，保留本地且不纳入提交。
- [x] 更新验证记录和计划状态；任务代码和独立验收已完成。

Git 收尾由主模型仅暂存任务文件，以 Conventional Commit 提交并 push 当前 main，确认 HEAD / upstream 同步。临时缓存因自动审批拒绝而保留，不暂存；最终实际 Git 结果在本次对话汇报，不把未跟踪缓存说成干净工作区。

## 验证命令

先按项目规则核对 `mise current`、`python --version`、`mise which python` 和 `uv --version`。正常 PowerShell profile 下已经确认为 mise Python 3.12.13；不使用跳过 profile 后命中商店别名的 shell 执行 Python。

在本次 PowerShell 进程设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1`，TMP / TEMP 为当前仓库规范绝对路径；启用 `AGENT_MANAGER_CODEX_TESTS=1`、`AGENT_MANAGER_CLAUDE_TESTS=1` 后执行：

```powershell
uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
git diff --check
```

已有客户端为 Codex CLI 0.162.0-alpha.17.2、Claude Code 2.1.296，均在既有精确版本测试范围内。真实 SSH、实际模型执行与日常客户端安装刷新不包含在本次无目标 / 无凭据的验收中。
