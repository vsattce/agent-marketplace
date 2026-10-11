# 自有 Skill 命名调整 Implementation Plan

> **For agentic workers:** 用户显式选择当前 `personal-dev:delegated-development`，覆盖通用执行方式建议；已授权生成文档后直接开工，不再次请求执行批准。主模型生成 spec / plan；一个 gpt-6-luna / xhigh 编码代理完成全部关联修改，另一干净上下文的 gpt-6-luna / max 独立验收，主模型终审并提交推送。子代理不得派生代理或 commit / push。

**Goal:** 将五个自有 Skill 改为 dev-delegate、dev-review、am-update、am-config、am-conflict，同步真实引用而保持所有业务行为。

**Architecture:** 原插件、目录发现根与客户端适配结构不变；仅重命名 Skill 及关联路径、名称和元数据。保持内部共享模型选择器与兼容并发锁，不加别名入口。

**Tech Stack:** Markdown、YAML / JSON、现有 Python unittest / PyYAML / tomlkit、Codex / Claude 隔离 loader、Kimi Node ASAR fixture；无新依赖。

**Spec:** docs/superpowers/specs/2026-10-11-owned-skill-naming-design.md

## Global Constraints

- 仅当前仓库自有两个插件及直接相关入口 / 文档 / 测试；第三方快照、sources / lock、开发辅助工具保持不变。
- personal-dev 仅 Codex / Claude，agent-manager 保持三端；所有现有手动、只读、项目写入及 BLOCKED 规则不变。
- `.configure-project.lock` 及其兼容测试保留；历史记录保留真实当时名称，现行链接及资源路径同步新位置。
- 不保证客户端 UI 的短词筛选；以已完成的原生加载证据与未验证 UI 行为分别汇报，不加 Router 或别名。
- Python 3.12+、mise / uv；当前已核验 Python 3.12.13、Node 24.19.0。无全局配置 / 缓存修改，不运行 Skill 业务操作。
- main 初始干净，基线见 spec；单一写入代理；验收覆盖全部未提交改动，最多两轮返工。

## Review Focus

1. dev-review 兄弟 helper 导入路径可用，输入输出及失败契约不变：已有 personal-dev helper 测试覆盖。
2. 新旧配置执行器共享同一旧锁且回滚、已有锁保护不变：既有 configure-project 测试覆盖。
3. 隐藏 manifest / agents/openai.yaml、普通 review 与实际 Skill 引用区分准确：packaging 和残留语义检查覆盖。
4. Kimi 不意外增加 personal-dev，管理入口新名称与资源复制一致：packaging / 原生 fixture 覆盖。
5. 历史记录不冒充新版本通过，旧链接不失效，第三方零修改：文档链接检查及累计 diff 验收覆盖。

## Task 1: 五个自有 Skill 的完整重命名

**Files:**
- Rename: plugins/personal-dev/skills/{delegated-development,review} → {dev-delegate,dev-review}
- Rename: plugins/agent-manager/skills/{check-updates,configure-project,resolve-conflicts} → {am-update,am-config,am-conflict}
- Modify: 对应 SKILL.md、agents/openai.yaml、自有脚本、references 与直接依赖路径。
- Modify as needed: plugins/{personal-dev,agent-manager}/plugin.json、plugins/agent-manager/kimi.plugin.json、.agents/plugins/marketplace.json、kimi.plugin.json；无必要不改 Claude 纯插件身份 manifest。
- Modify: tests/test_personal_dev*.py、test_agent_manager.py、test_configure_project.py、test_project_config_codex.py、test_codex_loader.py、test_claude_loader.py、test_sync.py、tests/kimi_loader.cjs 中实际关联契约。
- Modify: README.md、docs/usage.md、docs/maintenance.md 及历史记录内需要继续可用的文件链接。
- Evidence: docs/superpowers/reviews/2026-10-11-owned-skill-naming-validation.md；记录代理身份、实际验证、残留例外及修复次数。

**Interfaces:**
- 提供五个新名字的目录 / frontmatter / 显式调用；插件身份及 skills/ 发现目录不变。
- Python helper 公共函数、参数、输出、退出状态不变，只修资源路径和名称字符串；内部锁接口沿用 `.configure-project.lock`。

- [x] **Step 1: 基线与先行契约验证。** 先行包装 RED 命中 personal-dev 两项、agent-manager 一项，均因仍是旧目录布局而失败；确认新目录契约有效后实施重命名。跨盘逃逸 fixture 定向复验 1 项通过。
- [x] **Step 2: 重命名并修真实引用。** 五个自有目录、frontmatter、显式调用、脚本引用及加载 fixture 已同步；旧目录不再存在。公共业务逻辑和普通 review / 原生 `/review` 保持不变。
- [x] **Step 3: 包装与文档。** 已更新相关 catalog、版本、使用及维护说明；旧完整调用不保留别名，说明安装副本需刷新并重载或开新会话。历史记录保留原貌。
- [x] **Step 4: 验证。** 双端隔离全量 unittest 最终 133 项通过、exit 0；Claude Code 2.1.296、Codex CLI 0.162.0-alpha.17.2。Claude 根及两个自有插件校验 exit 0。Kimi Code 1.0.4 loader 5 项中 4 项通过、在线安装项显式 skip。完整记录见 [验证记录](../reviews/2026-10-11-owned-skill-naming-validation.md)。
- [x] **Step 5: 名称与范围检查。** 当前入口无旧名；允许残留仅为 `.configure-project.lock` 兼容路径、迁移/历史记录。原有 28 份相关 Markdown 的 80 个链接和锚点通过；新增验证记录链接单独确认目标存在。sources 与 source lock、第三方快照未改；`git diff --check` 通过。
- [x] **Step 6: 独立验收。** 干净上下文的 `/root/accept_owned_skill_rename`（gpt-6-luna / max）检查全部 staged / unstaged / 新文件，需求 PASS、质量 PASS、无阻塞项。UI 短词搜索为 UNVERIFIED，未用原生加载冒充 UI 实测；未触发返工。
- [x] **Step 7: 主模型终审与 Git 准备。** 已核对累计差异、必要新文件、验证证据与范围，补齐计划和验证记录。21 个 Skill 文件逐文件符合授权名称替换，资源树保留，现行旧名只剩兼容锁。提交与非强制推送 origin/main 在本记录保存后执行；此勾选仅记录终审和交付准备，实际提交哈希、远端 SHA 与工作区结果以最终聊天报告为准，不由勾选推断 Git 已完成。

## 执行记录

- 编码：gpt-6-luna / xhigh；独立验收：gpt-6-luna / max；独立验收和主模型终审均通过。
- 编码代理：`/root/rename_owned_skills`；验收代理：`/root/accept_owned_skill_rename`。
- 修复轮次：0 / 2。
- 实现、计划内验证、独立验收与终审完成；客户端 UI 短词筛选未实测，原生加载不代替 UI 验收。Git 收尾在保存此记录后由主模型执行，实际结果在最终聊天报告。
