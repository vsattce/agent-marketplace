# Codex 项目开关能力

2026-10-10，Windows 本机 `codex-cli 0.162.0-alpha.2` 的开发验收证据：`tests/test_project_config_codex.py`。测试的 CODEX_HOME、项目、安装缓存、localhost 加载捕获均是隔离 fixture；不修改日常用户配置，也不调用真实模型。此开发测试不属于 Skill 运行流程。

| 操作 | 当前支持 | 依据 |
| --- | --- | --- |
| 已安装本地 Marketplace Plugin 项目开关 | IMPLEMENTED | 根 `.codex/config.toml` 的 `[plugins."name@marketplace"] enabled = true/false`，新进程加载器确实按项目值覆盖用户值 |
| 单个 Skill 项目开关（standalone / Plugin Skill） | BLOCKED | `config/read` 能看到项目 `skills.config`，但 `skills/list` 的 enabled 不变；同一 `SKILL.md` 选择器在隔离用户层才生效。项目 true 也不能覆盖用户 false |
| standalone Skill 项目安装 | 手动复制可用 | 当前 Codex 项目 Skill 发现目录 `.agents/skills/`；只复制用户明确指定的来源，不使用可能写 CODEX_HOME 的安装器 |
| workspace-managed Plugin 项目开关 | BLOCKED | 官方说明项目配置不覆盖 workspace-managed 安装策略 |
| 未受信任项目 / 被更高配置限制的开关 | BLOCKED | 项目层未加载或不能决定最终状态，不改信任、安全、profile 或 managed 配置 |

Skill 目录复制是项目文件操作，不是单个 Skill 开关，也不证明 Plugin 可项目安装。写入前仍按 [项目文件预检](project-edits.md) 核验来源、目标、真实加载链、冲突和重复。

官方来源：

- [Plugin 项目级配置、稳定身份与覆盖边界](https://developers.openai.com/plugins/build/plugins)：只使用已有安装，绝不触发 Marketplace refresh；官方指出 refresh 可能安装/刷新 disabled Plugin，因而运行流程也禁止 refresh。
- [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)：`plugins.<plugin>.enabled` 使用 `plugin-name@marketplace-name`；项目必须 trusted；`skills.config` 虽已列为字段，字段可解析不代表项目加载器应用。
- [配置层级与信任](https://learn.chatgpt.com/docs/config-file/config-basic)：项目设置高于用户默认值，但受 CLI、profile、managed 限制；仅保存配置不能证明当前会话已刷新。
- [Skill 开关与显式调用](https://learn.chatgpt.com/docs/build-skills)：当前开关示例在用户 `~/.codex/config.toml`，path 为 `SKILL.md`；metadata 的 `policy.allow_implicit_invocation: false` 阻止隐式调用。

维护者换版本时先在隔离环境运行真实 loader 测试，再修改代码中的 VERIFIED_CODEX 与此表。不能根据 schema、config/read、文档通用层级推断单个 Skill 开关有效；不能通过用户级写入弥补项目能力缺失。Claude Code 使用 [独立 adapter 与证据](claude-support.md)。
