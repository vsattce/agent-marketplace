# Claude Code 项目开关能力

目标版本：Windows `2.1.296 (Claude Code)`。开发验收入口为 `tests/test_claude_loader.py`，配置编辑测试为 `tests/test_configure_project_claude.py`。隔离 `CLAUDE_CONFIG_DIR`、临时 Git 项目、插件安装及 localhost 请求捕获，不使用真实模型或日常用户配置。开发测试与 Skill 执行流程独立；Skill 运行时只读取现有证据，不启动 Claude 验证能力。

| 操作 | 支持边界 |
| --- | --- |
| 已安装 Marketplace Plugin 项目开关 | 根 `.claude/settings.json` 的 `enabledPlugins["name@marketplace"] = true/false`；项目值覆盖用户值 |
| `.claude/settings.local.json` 覆盖 | local 高于 project；同一目标存在反向值就整批 BLOCKED，不改 local 或全局兜底 |
| managed / CLI / excluded settings source / 未受信任项目 | 需要现有会话证明项目层有效、请求能决定最终状态，否则 BLOCKED |
| 单个 Plugin Skill | BLOCKED；官方说明 `skillOverrides` 不应用于 Plugin Skills |
| standalone Skill 项目安装 | 手动复制用户明确指定来源至 `.claude/skills/` 可用；仅只读来源，写入限于当前项目；不使用可能写用户 cache 的安装器 |
| 未安装或身份不明 Plugin / 未验证版本 | BLOCKED，不安装、不探测、不刷新 |

Skill 目录复制是项目文件操作，不是单个 Skill 开关，也不证明 Plugin 可项目安装。按 [项目文件预检](project-edits.md) 核验真实目录、来源、冲突和重复。

Claude Code `2.1.277+` 可按版本、当前 Project instructions 设置及工作目录祖先中的 `CLAUDE.md` / `CLAUDE.local.md` 选择是否读取 `AGENTS.md`；编辑前检查实际加载证据，不自动添加 import。官方加载细节见 [memory / AGENTS.md](https://code.claude.com/docs/en/memory)。

证据输入使用 `agent: "claude"`、`inventory.claude_version: "2.1.296 (Claude Code)"`；targets 的 Plugin 使用完整 `name@marketplace`、已存在 `.claude-plugin/plugin.json` 的真实插件根、`installed: true`、`configuration: "marketplace"`。同一身份有不同 scope / projectPath 时仅纳入适用当前项目的 receipt，歧义不猜选。版本、root、完整 inventory、有效项目层和覆盖断言均须来自当前环境。

配置按严格 UTF-8 JSON 处理：拒绝语法损坏、重复键、NaN / Infinity、非对象及非法 enabledPlugins 值，保留未请求值和无关字节；只对目标值增量替换，缺项时插入。新增字段的排版可以不同，但其他已有成员保持原字节。不支持 JSONC，不能把不能解析的配置视为空文件。

维护者换版本时先跑隔离加载器验收，再修改 `VERIFIED_CLAUDE` 和此说明。保存后需新会话或客户端重载；重新读配置不代表当前聊天已热加载。

官方依据（2026-10-10）：[设置来源与层级](https://code.claude.com/docs/en/settings)、[Plugin manifest](https://code.claude.com/docs/en/plugins-reference)、[Skill visibility 与 Plugin 限制](https://code.claude.com/docs/en/skills)。
