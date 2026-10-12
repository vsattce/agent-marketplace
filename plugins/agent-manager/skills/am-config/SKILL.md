---
name: am-config
disable-model-invocation: true
description: 编辑项目 Agent：仅在用户明确调用时，检查相关冲突并编辑项目 AGENTS.md、安装指定 Skill 或修改受支持的 Plugin 开关；也可只读查找冲突，轻微差异简述，实质冲突详细报告。
---

# 编辑项目 Agent 指令 / Skill / Plugin

项目编辑与冲突检查共用一个入口。只有用户明确调用 Codex 的 `$agent-manager:am-config` 或 Claude Code 的 `/agent-manager:am-config` 后才执行；其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。普通聊天、技术栈识别、配置问题或冲突发现均不能触发。

最高边界：只写当前项目；用户级、全局和项目外始终只读。不改 trust、安全、审批、model、reasoning、MCP 或 profile，不 commit / push，不刷新 Marketplace，不自动安装依赖。只执行用户明确要求的操作，不推荐组合。

## 按请求选择行为

- **编辑**：用户明确指定修改内容、安装来源/目标或 Plugin 开关时，先检查本次操作相关的冲突与重复，再执行下方编辑步骤。无关能力不展开扫描；若用户同时要求全面检查，再扩大检查范围。
- **只检查**：用户要求“只检查冲突、不修改”或仅要求查找冲突时，按 [冲突检查与分级输出](references/conflicts.md) 只读检查用户指定范围；未限定时检查当前项目适用的指令、Skills、Plugins 与相关全局来源。只在聊天中输出结果，不创建临时/报告文件，不调用配置编辑器，不安装、禁用或修改任何内容；报告后结束，不转入编辑步骤。冲突检查本身不要求 Windows 或 Python 编辑器环境。
- **请求不明确**：只调用入口但未说明要编辑什么或检查什么时，问一个决定范围的问题，不自行推断写入目标。“检查并修复”没有给出取舍时，先只读检查；存在会改变行为的多个方案时取得明确取舍后再编辑。

## 执行

1. 确认当前 Harness 为 Codex 或 Claude Code，再确认项目根和请求作用域；优先用当前 workspace / Git 根，不从模型品牌猜 Harness。其他或身份不明的 Harness 返回 `BLOCKED / UNSUPPORTED AGENT`。文件操作默认作用于根目录，只有用户明确给出子目录时才缩小作用域。Plugin 开关仍要求 Git 根；失败返回 `BLOCKED / PROJECT ROOT NOT FOUND`。不 git init、不切换项目。
2. 解析完整批次，只接受明确指定的项目操作：编辑项目 `AGENTS.md`、从明确来源复制 standalone Skill 到明确项目目标、安装用户明确指定的项目 Plugin，或本版支持的已安装 Plugin 开关。Plugin 安装仅在当前 Harness 的具体安装工具/操作、来源身份、canonical 目标及**全部写入都留在当前项目**均有当前证据时才执行；否则 `BLOCKED`。不把 Plugin 安装、Skill 安装或 `AGENTS.md` 编辑塞进 `configure_project.py` 的 stdin 契约。泛化配置文件编辑不在本 Skill 范围内。
3. 写入前按 [项目文件预检](references/project-edits.md) 对完整批次做只读预检，并按 [冲突检查与分级输出](references/conflicts.md) 比较相关规则：确认实际加载链、所有目标与来源，检查冲突、能力重复、路径和支持边界。Plugin 安装还必须核实当前版本真实支持的具体安装操作及其完整写入范围；仅有 `--scope project` 不足以证明安全。任何目标歧义、未解决冲突、无法归并的重复目标或完成操作所必需的加载/能力证据缺失，均先停止整批；按实际影响报告问题与最小选择，只问会改变结果的问题。用户已明确要求将既有规则从 A 改为 B 时，按该授权原位修改并去重，不重复询问；轻微提示不构成覆盖、删除或禁用其他能力的授权。
4. 批次含 Plugin 开关时，Codex 与 Claude Code 按各自 [支持边界](references/codex-support.md)、[Claude 证据](references/claude-support.md) 和 [编辑器输入](references/editor-input.md) 完成能力、版本、依赖核对并预备**仅开关请求**的编辑器输入；此步不调用会写入的 `scripts/configure_project.py`。保留编辑器原输入契约。纯 `AGENTS.md` 编辑或 standalone Skill 安装不需要 Python；单个 Skill 开关仍不支持。
5. 首次写入前重读全部目标并与预检基线比对；基线变化时停止并重新预检。复核通过后，才在已确认的项目路径内做最小编辑或完整复制，并对预备好的 Plugin 开关输入调用 `scripts/configure_project.py`。保留原文、编码、换行和用户已有改动；只改请求涉及的规则。Skill 安装保留所需资源并记录来源；不运行来源脚本或不受支持的原生安装器，不覆盖身份不明的已有文件。Plugin 安装只调用预检证据已确认的具体项目内操作，不自行猜测命令或改用复制伪装安装。
6. 写后重读目标，核对请求结果、无关内容和适用加载状态。Plugin 安装另核验安装记录、来源身份和实际项目作用域，并确认操作没有产生项目外写入；无法确认则报告 `BLOCKED` / `UNKNOWN`，不得声称安装成功。跨文件操作不是原子事务；执行中失败时只在当前文件仍与本次写入完全一致时恢复本次改动，遇到并发修改则保留现状并报告 `UNKNOWN; CHECK PROJECT FILES`。不把保存文件声称为当前会话已热加载。

## 支持边界

- **Plugin 项目开关**：编辑器仅在 Windows 运行；其他平台返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`。此限制只适用于 Plugin 开关，不影响 `AGENTS.md` 编辑或 standalone Skill 安装。Codex `0.162.0-alpha.17.2` / `0.162.0-alpha.2` 的已安装本地 Marketplace Plugin 写 `.codex/config.toml`；Claude Code `2.1.291` / `2.1.296` 写 `.claude/settings.json`。更高覆盖、managed 限制、信任或有效层证据不足时整批拒绝。Codex / Claude 的单个 Skill 项目开关仍为 `BLOCKED`。
- **项目 standalone Skill 安装**：仅按 Codex `.agents/skills/` 或 Claude Code `.claude/skills/` 的已确认发现目录处理，且来源和目标由用户明确指定。安装不等于启用 Plugin。
- **项目 Plugin 安装**：当前 Codex 与 Claude Code 均无全写入限于项目内的已验证安装契约，故 `BLOCKED / PROJECT-LOCAL PLUGIN INSTALL NOT VERIFIED`。其他 Harness 为 `BLOCKED / UNSUPPORTED AGENT`。项目 Plugin 开关证据不构成安装证据。
- **项目 `AGENTS.md`**：按 Codex 或 Claude Code 的真实指令链检查目标文件是否生效。Codex 同目录 `AGENTS.override.md` 会遮蔽 `AGENTS.md`；Claude 按版本、祖先 `CLAUDE.md` / `CLAUDE.local.md` 与 Project instructions 设置判断。可按用户明确要求编辑目标文件，但不自动改名、加引用或声称当前 Harness 会加载它。
- 其他 Harness 为 `BLOCKED / UNSUPPORTED AGENT`。若用户仅明确要求编辑 `AGENTS.md`，但 Codex / Claude Code 的加载状态未知，可完成文件编辑并报告 `LOADING UNKNOWN`；若用户要求让当前 Harness 确实遵循它，先问是否授权添加项目内引用/入口。

## 报告

日常成功简述修改结果与目标路径；无变化时说明 `UNCHANGED`。无冲突无需逐项报告预检；轻微差异用一两句话说明影响及处理依据。不确定的来源或加载状态写 `UNKNOWN` / `LOADING UNKNOWN`，检查不完整写 `PARTIAL`，不得声称已排除冲突或已生效。只检查时使用 [分级输出](references/conflicts.md)，不输出编辑成功。

阻止编辑时报告 `BLOCKED`、原因、目标及 `Changes applied: NONE`；实质冲突详细给出双方证据、共同条件、行为影响和最小方案，其他错误只给直接相关证据。如失败恢复被并发修改阻止，明确列出可能已改路径与 `UNKNOWN; CHECK PROJECT FILES`，不声称零修改。配置编辑器的结构化报告契约保持不变，聊天无需逐字段复述。
