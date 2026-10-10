# Claude Code 来源与只读更新检查

仅用于已确认的 Claude Code Harness。`/agent-manager:resolve-conflicts`、`/agent-manager:check-updates`、`/agent-manager:configure-project` 为手动入口；三个 Skill 的 `disable-model-invocation: true` 保留该限制，`agents/openai.yaml` 只控制 Codex。

## 来源与安装证据

- 配置根来自实际 `CLAUDE_CONFIG_DIR`，未设置时为 `~/.claude`。项目指令、rules、imports 的发现见 [Agent 来源说明](agent-sources.md)。
- Marketplace catalog 为 `.claude-plugin/marketplace.json`，插件 manifest 为 `.claude-plugin/plugin.json`，Skills 使用同一插件根 `skills/`。根 `plugin.json` 为 Codex 使用，不能拿其 version 代替 Claude manifest 的版本策略。
- 已存在的 `<config-root>/plugins/known_marketplaces.json` 记录 Marketplace source、缓存目录及更新时间；`installed_plugins.json` 记录插件完整 identity、scope、projectPath、installPath、version、gitCommitSha 等安装证据。字段须按当前版本实际文件核对；同一 identity 的不同 scope / projectPath 分别列出，不选择第一项。
- 启用状态按现有会话和有效配置核对：用户 `settings.json`、项目 `.claude/settings.json`、本地 `.claude/settings.local.json`、CLI `--settings` 和 managed 层。receipt 不证明当前会话加载；version 相同、缓存存在、源文件可读均不证明最新。

## 更新检查

先读现有 receipt / catalog / manifest，不运行 Claude Code 进程或 `/plugin` 界面做探测。`plugin list` / `details` 虽能查询信息，但不能保证初始化不写日志、注册或缓存，严格只读流程不调用；缺证据标 UNKNOWN。用户已有命令输出可作为证据。

源码根从用户指定位置或已记录 Marketplace source 确认。GitHub / Git 来源按原 repo/ref 查询精确 SHA；本地目录 source 读取真实 catalog 与文件指纹，标 `LOCAL SOURCE`。GitHub Marketplace 的已记录分支与 snapshot SHA 分别报告；缓存时间不等于当前远端 commit。不运行 marketplace update / plugin update / add / install / enable / disable，也不修改用户状态。

本仓库 Claude manifest 与 catalog 故意不写 version，Git 来源按 Marketplace commit 跟踪更新，避免第三方快照同步后被固定 `1.0.0` 阻挡。比较安装 `gitCommitSha` 与既定 Marketplace repo/ref；字段缺失或不可靠时用精确文件比较，否则 UNKNOWN。对本地 in-place 安装，source 内容可能直接生效，不能把安装时间误判为旧版本。远端新 commit 只说明市场版本变化；定位具体 Skill 时使用对应 sources/lock 或内容证据。

第三方来源比较继续使用共享 `check_sources.py`；OWNED 比较源码当前 branch / tracking remote 的 SHA 与 ancestry；两者遵循 check-updates 主流程。standalone 从现有会话、项目 `.claude/skills`、配置根 `skills` 和已确认额外目录发现；按真实来源与 provenance 分别列行。新版本也可能在用户 skills 下提供 Plugin；先核对 manifest，避免重复统计。没有来源的入口为 UNKNOWN SOURCE，不按同名 upstream 认领。

项目开关的写入能力另见 [Claude 支持证据](../skills/configure-project/references/claude-support.md)，本文件不授权配置修改。

官方依据（2026-10-10）：[Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[manifest](https://code.claude.com/docs/en/plugins-reference)、[版本策略](https://code.claude.com/docs/en/plugins/host-marketplace)、[配置层级与目录](https://code.claude.com/docs/en/settings)、[Skill 调用](https://code.claude.com/docs/en/skills)。
