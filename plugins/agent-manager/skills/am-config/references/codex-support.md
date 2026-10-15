# Codex 项目开关能力

已验证的开关编辑器版本为 `codex-cli 0.162.0-alpha.17.2` / `codex-cli 0.162.0-alpha.2`，Windows 验收入口：`tests/test_project_config_codex.py`。测试的 CODEX_HOME、项目、缓存和加载查询使用隔离 fixture，不改日常用户配置或调用真实模型。编辑请求可复用已有入口或按 [隔离加载验证](project-edits.md#隔离加载验证) 补充证据；独立只读检查不运行 fixture。

| 操作 | 当前支持 | 依据 |
| --- | --- | --- |
| 已安装本地 Marketplace Plugin 项目开关 | IMPLEMENTED | 根 `.codex/config.toml` 的 `[plugins."name@marketplace"] enabled = true/false`，新进程加载器确实按项目值覆盖用户值 |
| 项目 Plugin 文件准备、catalog 注册和开关保存 | 文件操作可用 | 官方支持项目插件目录、`.agents/plugins/marketplace.json` 和项目开关；不要求先有安装 receipt，也不通过已安装开关编辑器，实际发现/安装/加载分别核验 |
| 单个 Skill 项目开关（standalone / Plugin Skill） | BLOCKED | `config/read` 能看到项目 `skills.config`，但 `skills/list` 的 enabled 不变；同一 `SKILL.md` 选择器在隔离用户层才生效。项目 true 也不能覆盖用户 false |
| standalone Skill 项目安装 | 手动复制可用 | 当前 Codex 项目 Skill 发现目录 `.agents/skills/`；只复制用户明确指定的来源，不使用可能写 CODEX_HOME 的安装器 |
| workspace-managed Plugin 项目开关 | BLOCKED | 官方说明项目配置不覆盖 workspace-managed 安装策略 |
| 未受信任项目 / 被更高配置限制的开关 | BLOCKED | 项目层未加载或不能决定最终状态，不改信任、安全、profile 或 managed 配置 |

2026-10-15 在 `0.162.0-alpha.17.2` 的隔离 CLI fixture 中，仅添加项目 Plugin、repo catalog 和 `enabled=true`，未执行 Marketplace / Plugin 安装：`plugin list` 未发现该条目，`skills/list` 未加载 Plugin Skill，隔离用户配置保持不变。回归入口为 `ProjectLocalPreparationCodexTests`。这说明当前路径的“文件已准备 / 配置已保存”不能写成“实际加载已确认”；不据此否定文件准备或其他受支持客户端路径。

Skill 目录复制是项目文件操作，不是单个 Skill 开关，也不证明 Plugin 已安装。写入前仍按 [项目文件预检](project-edits.md) 核验来源、目标、加载链、冲突和重复。

官方来源：

- [Plugin 项目目录、catalog、稳定身份与覆盖边界](https://developers.openai.com/plugins/build/plugins)：允许按官方布局准备项目文件；目录发现与安装/加载须分开核验。日常 Marketplace refresh 可能安装/刷新 disabled Plugin，默认不触发；隔离验证按独立项目 fixture 执行。
- [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)：`plugins.<plugin>.enabled` 使用 `plugin-name@marketplace-name`；项目必须 trusted；`skills.config` 虽已列为字段，字段可解析不代表项目加载器应用。
- [配置层级与信任](https://learn.chatgpt.com/docs/config-file/config-basic)：项目设置高于用户默认值，但受 CLI、profile、managed 限制；仅保存配置不能证明当前会话已刷新。
- [Skill 开关与显式调用](https://learn.chatgpt.com/docs/build-skills)：当前开关示例在用户 `~/.codex/config.toml`，path 为 `SKILL.md`；metadata 的 `policy.allow_implicit_invocation: false` 阻止隐式调用。

维护者换版本时先在隔离环境运行真实 loader 测试，再修改代码中的 VERIFIED_CODEX_VERSIONS 与此表。不能根据 schema、config/read、文档通用层级推断单个 Skill 开关有效；不能通过用户级写入弥补项目能力缺失。Claude Code 使用 [独立 adapter 与证据](claude-support.md)。
