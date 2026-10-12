# Claude Code 来源与加载规则

仅用于已确认的 Claude Code Harness。供 `/agent-manager:am-config` 执行只读冲突检查与编辑预检时使用；`am-config` 按当前请求判断配置；`disable-model-invocation: true` 保留对应手动调用限制，`agents/openai.yaml` 只控制 Codex。

## 来源与安装证据

- 配置根来自实际 `CLAUDE_CONFIG_DIR`，未设置时为 `~/.claude`。全局来源包括 `~/.claude/CLAUDE.md` 与 `~/.claude/rules/`；项目来源包括 cwd 及祖先的 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md` 与 `.claude/rules/`。跟进适用的 `@path` 引用，按 `paths` 和子目录条件记录作用域；项目根外祖先单列为继承来源。内容通常合并，不能套用 Codex“每层首个文件”规则，也不能假定项目规则会消除所有全局要求。检查 exclusions、managed 层和项目指令设置后，再记录实际适用的来源。
- `CLAUDE.md` 是主要入口，但较新版本可按版本、项目指令设置与 CLAUDE 文件是否存在选择加载 `AGENTS.md`；也可通过 `CLAUDE.md` 导入。执行时核对实际版本、配置与会话证据。
- Skills 从当前会话、项目 `.claude/skills`、用户 `~/.claude/skills`、Plugin 或有效兼容 commands / 额外路径发现。调用策略按 Claude 规范解释，`agents/openai.yaml` 不作为 Claude 启用证据。Plugin 身份、安装 scope、启用层及 hooks / agents / MCP 等能力结合 manifest、receipt 和有效 settings 核对。
- Marketplace catalog 为 `.claude-plugin/marketplace.json`，插件 manifest 为 `.claude-plugin/plugin.json`，Skills 使用同一插件根 `skills/`。根 `plugin.json` 为 Codex 使用，不能拿其 version 代替 Claude manifest 的版本策略。
- 已存在的 `<config-root>/plugins/known_marketplaces.json` 记录 Marketplace source、缓存目录及更新时间；`installed_plugins.json` 记录插件完整 identity、scope、projectPath、installPath、version、gitCommitSha 等安装证据。字段须按当前版本实际文件核对；同一 identity 的不同 scope / projectPath 分别列出，不选择第一项。
- 启用状态按现有会话和有效配置核对：用户 `settings.json`、项目 `.claude/settings.json`、本地 `.claude/settings.local.json`、CLI `--settings` 和 managed 层。receipt、version 相同、缓存存在或源文件可读均不证明当前会话加载。

## 只读取证

先读现有 receipt / catalog / manifest，不运行 Claude Code 进程或 `/plugin` 界面做探测。`plugin list` / `details` 虽能查询信息，但不能保证初始化不写日志、注册或缓存，严格只读流程不调用；缺证据标 UNKNOWN。用户已有命令输出可作为证据。

只读检查不运行 marketplace update / plugin update / add / install / enable / disable，也不修改用户状态。standalone 从现有会话、项目 `.claude/skills`、配置根 `skills` 和已确认额外目录发现，按实际来源去重；先核对 manifest，避免把 Plugin 缓存或源码误认为 standalone 入口。来源未知时标 `UNKNOWN`，不按同名 upstream 认领。

项目开关的写入能力另见 [Claude 支持证据](../skills/am-config/references/claude-support.md)，本文件不授权配置修改。

官方依据（2026-10-10）：[Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[manifest](https://code.claude.com/docs/en/plugins-reference)、[版本策略](https://code.claude.com/docs/en/plugins/host-marketplace)、[配置层级与目录](https://code.claude.com/docs/en/settings)、[Skill 调用](https://code.claude.com/docs/en/skills)。
