---
name: am-config
disable-model-invocation: true
description: Use when explicitly called to edit project AGENTS.md files, install user-specified project Skills or Plugins, or change a supported project Plugin switch. Only use when explicitly invoked by the user.
---

# 配置当前项目的 Agent 指令 / Skill / Plugin

纯执行型项目配置入口。只有用户明确调用 Codex 的 `$agent-manager:am-config`、Claude Code 的 `/agent-manager:am-config`、Kimi Code 的 `/skill:am-config`（或当前客户端支持的显式别名）后才执行。普通聊天、技术栈识别、配置问题或冲突发现均不能触发，也不从 `am-conflict` 自动转入。

最高边界：只写当前项目；用户级、全局和项目外始终只读。不改 trust、安全、审批、model、reasoning、MCP 或 profile，不 commit / push，不刷新 Marketplace，不自动安装依赖。只执行用户明确要求的操作，不推荐组合。

## 执行

1. 按当前 Harness 身份确认项目根和请求作用域；优先用当前 workspace / Git 根，不从模型品牌猜 Harness。文件操作默认作用于根目录，只有用户明确给出子目录时才缩小作用域。Plugin 开关仍要求 Git 根；失败返回 `BLOCKED / PROJECT ROOT NOT FOUND`。不 git init、不切换项目。
2. 解析完整批次，只接受明确指定的项目操作：编辑项目 `AGENTS.md`、从明确来源复制 standalone Skill 到明确项目目标、安装用户明确指定的项目 Plugin，或本版支持的已安装 Plugin 开关。Plugin 安装仅在当前 Harness 的具体安装工具/操作、来源身份、canonical 目标及**全部写入都留在当前项目**均有当前证据时才执行；否则 `BLOCKED`。不把 Plugin 安装、Skill 安装或 `AGENTS.md` 编辑塞进 `configure_project.py` 的 stdin 契约。泛化配置文件编辑不在本 Skill 范围内。
3. 写入前按 [项目文件预检](references/project-edits.md) 对完整批次做只读预检：确认实际加载链、所有目标与来源，检查冲突、能力重复、路径和支持边界。Plugin 安装还必须核实当前版本真实支持的具体安装操作及其完整写入范围；仅有 `--scope project` 不足以证明安全。任何目标歧义、未解决冲突、无法归并的重复目标或完成操作所必需的加载/能力证据缺失，均先停止整批；给出双方证据与最小选择，只问会改变结果的问题。用户已明确要求将既有规则从 A 改为 B 时，按该授权原位修改并去重，不重复询问。
4. 批次含 Plugin 开关时，Codex 与 Claude Code 按各自 [支持边界](references/codex-support.md)、[Claude 证据](references/claude-support.md) 和 [编辑器输入](references/editor-input.md) 完成能力、版本、依赖核对并预备**仅开关请求**的编辑器输入；此步不调用会写入的 `scripts/configure_project.py`。保留编辑器原输入契约。纯 `AGENTS.md` 编辑或 standalone Skill 安装不需要 Python，也不走单个 Skill 开关的 unsupported 分支。Kimi Plugin 开关不支持；含此请求的混合批次整批零写入。
5. 首次写入前重读全部目标并与预检基线比对；基线变化时停止并重新预检。复核通过后，才在已确认的项目路径内做最小编辑或完整复制，并对预备好的 Plugin 开关输入调用 `scripts/configure_project.py`。保留原文、编码、换行和用户已有改动；只改请求涉及的规则。Skill 安装保留所需资源并记录来源；不运行来源脚本或不受支持的原生安装器，不覆盖身份不明的已有文件。Plugin 安装只调用预检证据已确认的具体项目内操作，不自行猜测命令或改用复制伪装安装。
6. 写后重读目标，核对请求结果、无关内容和适用加载状态。Plugin 安装另核验安装记录、来源身份和实际项目作用域，并确认操作没有产生项目外写入；无法确认则报告 `BLOCKED` / `UNKNOWN`，不得声称安装成功。跨文件操作不是原子事务；执行中失败时只在当前文件仍与本次写入完全一致时恢复本次改动，遇到并发修改则保留现状并报告 `UNKNOWN; CHECK PROJECT FILES`。不把保存文件声称为当前会话已热加载。

## 支持边界

- **Plugin 项目开关**：Codex `0.162.0-alpha.17.2` / `0.162.0-alpha.2` 的已安装本地 Marketplace Plugin 写 `.codex/config.toml`；Claude Code `2.1.291` / `2.1.296` 写 `.claude/settings.json`。更高覆盖、managed 限制、信任或有效层证据不足时整批拒绝。Codex / Claude 的单个 Skill 项目开关仍为 `BLOCKED`。
- **项目 standalone Skill 安装**：仅按当前 Harness 已确认的项目发现目录处理，且来源和目标由用户明确指定。Codex 常见目录为 `.agents/skills/`，Claude 为 `.claude/skills/`，Kimi 为 `.kimi-code/skills/` 或 `.agents/skills/`；仍须按当前版本和配置核实。安装不等于启用 Plugin。
- **项目 Plugin 安装**：本版没有 Codex、Claude Code 或 Kimi Code 的全写入均限于项目内的已验证安装契约，故 `BLOCKED / PROJECT-LOCAL PLUGIN INSTALL NOT VERIFIED`。项目 Plugin 开关证据不构成安装证据。
- **项目 `AGENTS.md`**：按当前 Harness 的真实指令链检查目标文件是否生效。Codex 同目录 `AGENTS.override.md` 会遮蔽 `AGENTS.md`；Claude 按版本、祖先 `CLAUDE.md` / `CLAUDE.local.md` 与 Project instructions 设置判断；Kimi 按实际 `.kimi-code/AGENTS.md`、`AGENTS.md` 等项目来源判断。可按用户明确要求编辑目标文件，但不自动改名、加引用或声称当前 Harness 会加载它。
- 未验证的 Plugin 开关版本或其他 Harness 的安装能力为 `BLOCKED / UNSUPPORTED AGENT`。若用户仅明确要求编辑 `AGENTS.md`，但当前 Harness 的加载状态未知，可完成文件编辑并报告 `LOADING UNKNOWN`；若用户要求让当前 Harness 确实遵循它，先问是否授权添加项目内引用/入口。

## 报告

成功报告 `SUCCESS`、Agent、Project、每项操作与路径、Changed / Unchanged、加载状态和 `Global files modified: NONE`。不确定的来源或加载状态写 `UNKNOWN`，不得声称已排除冲突或已生效。

阻止时报告 `BLOCKED`、Reason、Target、相关来源证据及 `Changes applied: NONE`。如失败恢复被并发修改阻止，明确列出可能已改路径与 `UNKNOWN; CHECK PROJECT FILES`，不声称零修改。
