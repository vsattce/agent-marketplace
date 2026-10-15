# Claude Code 项目开关能力

已验证的开关编辑器版本：Windows `2.1.291 (Claude Code)` / `2.1.296 (Claude Code)`。加载验收入口为 `tests/test_claude_loader.py`，配置编辑测试为 `tests/test_configure_project_claude.py`。隔离 `CLAUDE_CONFIG_DIR`、临时项目、插件安装及 localhost 请求捕获，不使用真实模型或日常用户配置。编辑请求可按 [隔离加载验证](project-edits.md#隔离加载验证) 补充证据；独立只读检查不启动 fixture。

| 操作 | 支持边界 |
| --- | --- |
| 已安装 Marketplace Plugin 项目开关 | 根 `.claude/settings.json` 的 `enabledPlugins["name@marketplace"] = true/false`；项目值覆盖用户值 |
| 项目 Plugin 文件准备与注册配置 | 来源和格式确认后可准备完整 Plugin、项目 catalog / 已核实的发现入口及项目开关；不要求预先已安装，实际安装/加载另行核验 |
| `.claude/settings.local.json` 覆盖 | local 高于 project；同一目标存在反向值就整批 BLOCKED，不改 local 或全局兜底 |
| managed / CLI / excluded settings source / 未受信任项目 | 需要现有会话证明项目层有效、请求能决定最终状态，否则 BLOCKED |
| 单个 Plugin Skill | BLOCKED；官方说明 `skillOverrides` 不应用于 Plugin Skills |
| standalone Skill 项目安装 | 手动复制用户明确指定来源至 `.claude/skills/` 可用；仅只读来源，写入限于当前项目；不使用可能写用户 cache 的安装器 |
| 未安装 Plugin | 不通过已安装开关编辑器，按项目文件准备和隔离验证路径处理；不据此结束整个请求 |
| 身份不明 Plugin / 未验证版本 | 身份不明时停止相关写入；未知版本不调用该编辑器，按当前官方说明或隔离证据判断文件准备与加载能力 |

Skill / Plugin 目录准备是项目文件操作，不证明 Plugin 已安装或加载。原生安装的项目 scope 可能与缓存、receipt 的写入位置不同；按实际写入范围决定是否执行，不自动写用户配置或改成全局安装。按 [项目文件预检](project-edits.md) 核验来源、项目发现入口、冲突和重复。

Claude Code `2.1.277+` 可按版本、当前 Project instructions 设置及工作目录祖先中的 `CLAUDE.md` / `CLAUDE.local.md` 选择是否读取 `AGENTS.md`；编辑前检查实际加载证据，不自动添加 import。官方加载细节见 [memory / AGENTS.md](https://code.claude.com/docs/en/memory)。

证据输入使用 `agent: "claude"`、`inventory.claude_version` 为本轮实际版本（如 `"2.1.291 (Claude Code)"`），且属于已验证精确版本集合；targets 的 Plugin 使用完整 `name@marketplace`、已存在 `.claude-plugin/plugin.json` 的真实插件根、`installed: true`、`configuration: "marketplace"`。同一身份有不同 scope / projectPath 时仅纳入适用当前项目的 receipt，歧义不猜选。版本、root、完整 inventory、有效项目层和覆盖断言均须来自当前环境。

配置按严格 UTF-8 JSON 处理：拒绝语法损坏、重复键、NaN / Infinity、非对象及非法 enabledPlugins 值，保留未请求值和无关字节；只对目标值增量替换，缺项时插入。新增字段的排版可以不同，但其他已有成员保持原字节。不支持 JSONC，不能把不能解析的配置视为空文件。

维护者换版本时先跑隔离加载器验收，再修改 `VERIFIED_CLAUDE_VERSIONS` 和此说明。保存后需新会话或客户端重载；重新读配置不代表当前聊天已热加载。

官方依据（2026-10-10）：[设置来源与层级](https://code.claude.com/docs/en/settings)、[Plugin manifest](https://code.claude.com/docs/en/plugins-reference)、[Skill visibility 与 Plugin 限制](https://code.claude.com/docs/en/skills)。
