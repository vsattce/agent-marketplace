# Codex 来源与加载规则

适用于已确认的 Codex Harness。供手动入口 `$agent-manager:am-config` 执行只读冲突检查与编辑预检时使用；此文件不授权修改配置或运行探测。本机配置由 `am-config` 按当前请求读取和判断。官方规则用于解释加载方式；文档无法访问时保留静态检查并标明未知机制。

## 冲突查找

- 指令：实际 `CODEX_HOME`（未设置时通常 `~/.codex`）的全局指令，以及项目根到 cwd 的指令链。每层按 `AGENTS.override.md`、`AGENTS.md`、配置的 `project_doc_fallback_filenames` 查首个非空入口，不把同目录所有文件当作同时加载；注意 `project_doc_max_bytes` 截断与会话启动后文件变更。更深目录的规则仅对其作用域分析。
- `CLAUDE.md` 不是 Codex 的默认项目指令入口。只有已配置为 fallback、被有效规则引用或会话明确加载时才纳入；不能因为它在磁盘上存在就判为 Codex 冲突。
- Skills：以当前会话实际暴露的入口为准，结合项目根到 cwd 的 `.agents/skills`、用户 `.agents/skills`、会话列出的 `.codex/skills` 或自定义路径、系统入口及 Plugin 提供的 Skills 查来源。读取 frontmatter、正文和 `agents/openai.yaml`；`policy.allow_implicit_invocation: false` 表示仅手动。可用清单不表示每个 Skill 正文都已加载。
- Plugins：读取实际 manifest、安装 receipt / metadata、项目/用户 Marketplace 与相关启用配置。源码路径、Marketplace 收录、安装缓存和会话启用分别记录。项目控制通常来自 `.codex/config.toml`，用户控制来自 `$CODEX_HOME/config.toml`，但还须核对 trust、profile、CLI override 和 managed requirements；配置存在不证明当前会话加载。
- 优先级：全局到项目、由浅到深的指令链可对同一主题作更具体覆盖，仍受当前明确任务与上级规则约束。指令优先级与 Plugin/Skill 配置优先级分别核实，不能由文件所在层级推出所有入口的统一胜者。

官方依据（2026-10-10 核对；执行时有机制疑问再核对当前文档）：

- [AGENTS.md 发现、覆盖与 fallback](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Skill 来源、调用与配置](https://learn.chatgpt.com/docs/build-skills)
- [Plugin 结构与项目配置](https://developers.openai.com/plugins/build/plugins)
- [配置层级与信任](https://learn.chatgpt.com/docs/config-file/config-basic)
- [配置字段](https://learn.chatgpt.com/docs/config-file/config-reference)

优先读已有会话的清单与文件。若现有工具可无副作用地返回 `skills/list`、`config/read` 或 Plugin 状态，再按实际协议查询；不猜请求格式，不输出可能含密钥的完整配置。不启动新 Codex / app-server，不安装测试 Plugin，不写临时 CODEX_HOME，也不执行 disable filtering 验证。无法取得加载证据时，相关项为 `UNKNOWN`，静态分析继续。

调用使用完整入口 `$agent-manager:am-config`；裸别名是否可用以当前会话为准，不通过复制 standalone Skill 或修改配置补别名。项目开关写入能力见 [Codex 支持证据](../skills/am-config/references/codex-support.md)。
