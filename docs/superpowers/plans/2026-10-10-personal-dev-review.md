# Codex 增强代码审查 Implementation Plan

> **For agentic workers:** 本任务由用户显式选择 `personal-dev:delegated-development` 执行，覆盖通用执行方式建议。主模型编写 spec / plan；`gpt-6-luna` / `xhigh` 实现，另一个干净上下文的同型号 / `max` 独立验收，主模型终审。子代理不 commit / push，不继续派生代理。

**Goal:** 交付仅手动调用、带起步预检、委派审查与独立复核、分级降噪报告的 Codex 增强代码审查技能。

**Architecture:** `review/SKILL.md` 维护预检与编排；专项、角色和报告格式按需引用。轻量 adapter 复用兄弟技能的模型选择算法，只转换审查角色名称。保持一个写入代理，所有实现作为一个可独立验收的交付单元。

**Tech Stack:** Markdown、YAML / JSON、Python 3.12+ 标准库 helper、现有 unittest / PyYAML 与隔离 Codex loader。无新项目依赖，无全局配置修改。

**Spec:** `docs/superpowers/specs/2026-10-10-personal-dev-review-design.md`

## Global Constraints

- 仅用户显式调用，仅支持 Codex；Claude Code、Kimi 和其他 Agent 本次不适配。
- 主模型保持当前对话模型；审查 `xhigh`、独立复核 `max`，同大版本最新可用 Luna，实际名单校验后展示。
- 当前开发会话只改任务相关文件；未来 review 执行中代码/配置/Git 只读，仅报告及必要同目录记录可写，不自动修复或提交。
- 必需条件在正式派发前集中预检，缺失则 BLOCKED；可选实测数据缺失不阻塞普通静态审查。
- P0/P1 有证据且独立复核，P2 简述、P3 合并；纯风格默认不报。执行状态与风险等级分开。
- Python 使用已核实的 mise 3.12.13 解释器及 uv；不安装/切换运行时。不依赖 Node。
- 当前工作区初始干净；基线 `5c29f101724b0da1c934c6747ed9db3995f8203b`，当前 `main`，origin 为本仓库 GitHub。

## Review Focus

1. 模型来源不可靠/能力缺失时，必须在派发前一次 BLOCKED；helper 测试与起步阻塞演练覆盖。
2. 正常有限缓存、必要日志及配额未知请求不可升级；降噪演练覆盖正常反例与真实无界增长正例。
3. 显式目录/主题不能扩成全仓扫描；无 diff 的默认全项目审查不能跳过存量代码；范围演练覆盖。
4. 无生产证据时允许静态审查，待验证项与已确认发现分开；报告状态不因发现 P0/P1 变 BLOCKED；演练覆盖。
5. Plugin 新入口仅手动发现与注入，helper/refs 随包可用；现有开发入口和其他客户端不变；packaging 与隔离 loader 覆盖。

## Task 1: 完整技能与包装

**Files:**
- Create: `plugins/personal-dev/skills/review/SKILL.md`
- Create: `plugins/personal-dev/skills/review/agents/openai.yaml`
- Create: `plugins/personal-dev/skills/review/scripts/select_models.py`
- Create: `plugins/personal-dev/skills/review/references/review-contract.md`
- Create: `plugins/personal-dev/skills/review/references/report-template.md`
- Create: `tests/test_personal_dev_review.py`
- Modify: `plugins/personal-dev/plugin.json`, `.agents/plugins/marketplace.json`
- Modify: `tests/test_personal_dev_packaging.py`, `tests/test_personal_dev_loader.py`
- Modify: `README.md`, `docs/usage.md`, `docs/maintenance.md`
- Evidence: `docs/superpowers/reviews/2026-10-10-personal-dev-review-validation.md`

**Interfaces:**
- 输入：复用兄弟 helper 的 `primary_model` / `primary_model_source` / `inventory_source` / `models` / `model_override` / `override_confirmed`；新增 `audit_effort`、`verification_effort` 仅映射到原 `coding_effort`、`review_effort`，禁止混用旧角色字段。
- 成功：JSON `status=READY`，`audit={model,effort}`、`verification={model,effort}`、`display` 两行审查/复核实际值，exit 0。
- 失败：JSON `status=BLOCKED`、`reasons`，exit 2；不回显输入，不泄露异常路径、payload 或秘密。兄弟 helper 缺失/不可加载时同样安全 BLOCKED。
- runtime skill 只引用 helper 文件，不调用另一个显式技能；选择算法保持唯一来源。

- [x] **Step 1: 基线与需求决策演练**
  主模型安排干净上下文的无技能控制组，记录对正常缓存/日志、全项目无 diff、必需模型身份缺失和可选生产证据缺失的自然判断。先完成 spec 可实施性只读检查，再派发实现。实现前运行现有 personal-dev 测试已通过：24 个，1 个 opt-in skip。

- [x] **Step 2: 针对 helper 与包装先写测试并确认 RED**
  adapter 测试覆盖：角色输出、默认/覆写强度、同代最高版本、缺少身份或能力、非法输入/未知字段、旧字段混用、兄弟资源缺失、CLI 成功/失败输出。packaging 期望两个技能、`0.2.0`、手动策略和引用存在。执行 `uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -p "test_personal_dev*.py" -v`，新增功能未实现导致预期失败。

- [x] **Step 3: 实现 helper 与技能流程**
  写最小 adapter 复用已有选择函数并安全处理不可加载资源。SKILL 先预检再展示模型/派发，引用 contract 交接审查与复核职责、专项/分级规则和去重；引用 report-template 规定唯一报告路径、执行状态、证据与覆盖情况。用户输入不足时统一 BLOCKED，真实候选最多一轮定向补证。

- [x] **Step 4: 同步包装和文档**
  Codex manifest / catalog metadata 保持一致，Plugin 版本 `0.2.0`；Codex 总数 18 Skills，personal-dev 2，Claude/Kimi 保持原数。README / 使用说明包含调用示例与边界；维护说明包含新测试入口与实际验证边界。不要改 sources/lock 或旧开发 helper。

- [x] **Step 5: GREEN 与真实隔离加载**
  跑直接相关 personal-dev 测试；用现有隔离 CODEX_HOME / localhost provider 开启 `AGENT_MANAGER_CODEX_TESTS=1`，只跑 `test_personal_dev_loader.py`，验证两个入口被发现、普通提示不注入、显式 `$personal-dev:review` 注入正文。只改命令局部环境，不改日常缓存或配置。

- [x] **Step 6: 有技能行为演练与独立验收**
  主模型安排与控制组对应的独立决策演练；记录具体结果，出现实际偏差定向修正。增加明确范围/无 diff、可选生产证据缺失、有 P0/P1 候选需独立复核、无候选跳过复核、复核证实不成立时驳回/证据不足时转待验证，以及对应执行状态的场景。独立 `gpt-6-luna/max` 验收 spec / plan、实际未提交改动和新文件、既有证据。验收代理不重复全量测试；初次实现后的修复 + 独立复验最多两轮，保存计数。

- [x] **Step 7: 主模型终审与交付准备**
  主模型核实累计差异和 spec 覆盖；跑现有全量 unittest（真实模型客户端测试保持 opt-in），检查 `git diff --check` 和无关改动，更新此计划与验证记录。此勾选记录提交前已完成的检查；随后仅主模型按 Conventional Commits 提交并推送当前 `main`，核实远程 SHA 和工作区干净，实际 Git 结果在最终聊天报告，不能由计划勾选推断远端同步成功。

## 执行记录

- 主模型：`gpt-6.1-sol / xhigh`，来源为本轮 thread 的 turn_context；实际派发名单通过现有 helper 返回 READY。
- 编码：`gpt-6-luna / xhigh`；验收：`gpt-6-luna / max`。
- 修复轮次：1 / 2。子代理身份、测试与裁决记录于验证文档。
- 独立复验：需求覆盖 PASS、质量 PASS；主模型累计终审通过。已完成 5 组控制、5 组有技能和 5 个 READY 决策场景，全量 121 项（7 skip）及原生 personal-dev loader 通过；限制详见验证记录。
