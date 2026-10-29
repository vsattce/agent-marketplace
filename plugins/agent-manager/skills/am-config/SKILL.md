---
name: am-config
disable-model-invocation: true
description: 编辑项目 Agent：仅在用户明确调用时，检查相关冲突，编辑项目 AGENTS.md、安装指定 Skill、准备和注册项目 Plugin 或修改 Plugin 项目开关；区分配置保存与实际加载，也可只读查找冲突。
---

# 编辑项目 Agent 指令 / Skill / Plugin

项目编辑与冲突检查共用一个入口。只有用户明确调用 Codex 的 `$agent-manager:am-config`、Claude Code 的 `/agent-manager:am-config` 或 agy / dsh 桌面版的 `/am-config` 后才执行；其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。普通聊天、技术栈识别、配置问题或冲突发现均不能触发。

确认当前 Harness 为 dsh 桌面版时，读取 [dsh 适配](../../references/dsh.md)，按其项目编辑与只读检查分支执行并结束；下方 Codex / Claude 编辑器不用于 dsh，不修改桌面用户 profile。

确认当前 Harness 为 agy 时，读取 [agy 适配](../../references/agy.md)，按其项目编辑与只读检查分支执行并结束；下方 Codex / Claude 配置编辑器流程不用于 agy。入口仍仅手动调用，不能仅凭 frontmatter 推断 agy 已强制手动门控。

默认只写当前项目，日常用户配置与项目外来源只读。不改日常 trust、安全、审批、model、reasoning、MCP 或 profile，不 commit / push、不刷新日常 Marketplace、不自动安装依赖。隔离验证的配置、缓存、安装记录和日志全部留在项目临时目录。只执行用户明确要求的操作，不自动转向“全局安装、全局关闭、项目开启”；用户已有明确授权不重复询问。

## 按请求选择行为

- **编辑**：用户明确指定修改内容、安装来源/目标或 Plugin 开关时，先检查本次操作相关的冲突与重复，再执行下方编辑步骤。Plugin 尚未安装时，进入项目内准备与注册路径，不仅因 `installed=false` 结束任务。无关能力不展开扫描；若用户同时要求全面检查，再扩大检查范围。
- **只检查**：用户要求“只检查冲突、不修改”或仅要求查找冲突时，按 [冲突检查与分级输出](references/conflicts.md) 只读检查用户指定范围；未限定时检查当前项目适用的指令、Skills、Plugins 与相关全局来源。只在聊天中输出结果，不创建临时/报告文件，不调用配置编辑器，不安装、禁用或修改任何内容；报告后结束，不转入编辑步骤。冲突检查本身不要求 Windows 或 Python 编辑器环境。
- **请求不明确**：只调用入口但未说明要编辑什么或检查什么时，问一个决定范围的问题，不自行推断写入目标。“检查并修复”没有给出取舍时，先只读检查；存在会改变行为的多个方案时取得明确取舍后再编辑。

## 执行

1. 确认当前 Harness 为 Codex 或 Claude Code，再确认项目根和请求作用域；优先用当前 workspace / Git 根，不从模型品牌猜 Harness。其他或身份不明的 Harness 返回 `BLOCKED / UNSUPPORTED AGENT`。文件操作默认作用于根目录，只有用户明确给出子目录时才缩小作用域。Plugin 开关仍要求 Git 根；失败返回 `BLOCKED / PROJECT ROOT NOT FOUND`。不 git init、不切换项目。
2. 解析请求，区分项目 `AGENTS.md` 编辑、指定来源的 standalone Skill 安装、项目 Plugin 文件准备/注册及已安装 Plugin 开关。项目 Plugin 路径允许在已确认的项目目录内保留完整插件资源，编辑项目 Marketplace 条目和对应插件开关；其他配置字段不在范围内。`configure_project.py` 仍只处理已安装 Plugin 开关，不把准备、注册或安装动作塞进它的 stdin，也不伪造 `installed=true`。
3. 写入前按 [项目文件预检](references/project-edits.md) 检查来源身份、目标路径、直接相关冲突与重复。来源不明、目标歧义、未决实质冲突或可能越界写入时停止相关批次；实际加载尚未确认时，先核对当前官方路径，必要时做隔离验证，不能把未知直接等同于平台不支持。加载未知不阻止已明确授权且路径、来源和配置格式已确认的项目内准备；只问会改变结果的问题。用户已明确要求 A→B 时直接原位修改，不重复询问。
4. 已安装 Plugin 的开关按 [Codex](references/codex-support.md)、[Claude](references/claude-support.md) 和 [编辑器输入](references/editor-input.md) 核对有效层、能力及依赖，再预备编辑器输入。新准备 Plugin 的项目目录、catalog 和开关用文件工具最小编辑，不套用该编辑器的已安装门槛；配置格式和身份必须有官方或当前实现依据。纯文件准备不需要 Python；单个 Skill 项目开关仍不支持。
5. 首次写入前重读全部目标并与预检基线比对，变化时重新预检。保留原文、编码、换行和用户改动；只改请求涉及的文件与条目。安装器仅在其写入范围已确认符合授权时调用。官方描述的项目目录复制与 catalog 注册可以用于文件准备，但不作为已安装或已加载的证据。
6. 写后重读目标，分别核对文件准备、项目注册、配置保存及实际加载。缺少加载证据时按 [隔离验证](references/project-edits.md#隔离加载验证) 继续取证，并按该节记录后台 ID、确认验证进程退出后清理 fixture；若仍无法加载，报告具体缺项和已保存路径，不声称插件已启用。旧 Skills / 入口只有在替代入口的实际加载已确认且迁移授权明确时才移除。跨文件操作不是原子事务；失败时只恢复仍与本次写入完全一致的文件，遇到并发修改保留现状并报告 `UNKNOWN; CHECK PROJECT FILES`。不声称当前会话已热加载。

## 支持边界

- **已安装 Plugin 开关编辑器**：仅在 Windows 及已验证版本运行：Codex `0.162.0-alpha.17.2` / `0.162.0-alpha.2` 写 `.codex/config.toml`，Claude Code `2.1.291` / `2.1.296` 写 `.claude/settings.json`。其他平台、未知版本或有效层证据不足时不调用此编辑器；这不是项目文件准备的禁令，也不代表客户端一定不支持。Codex / Claude 的单个 Skill 项目开关仍为 `BLOCKED`。
- **项目 standalone Skill 安装**：仅按 Codex `.agents/skills/` 或 Claude Code `.claude/skills/` 的已确认发现目录处理，且来源和目标由用户明确指定。安装不等于启用 Plugin。
- **项目 Plugin 准备与注册**：在来源、项目路径和文件格式确认后可完成插件资源、项目 catalog 与对应开关；实际安装和加载另行核验。原生安装器可能写用户级记录，不能因 `--scope project` 就调用，也不预设必须全局安装。需要项目外写入时停止该安装操作，保留已授权的准备结果并说明限制。
- **项目 `AGENTS.md`**：按 Codex 或 Claude Code 的真实指令链检查目标文件是否生效。Codex 同目录 `AGENTS.override.md` 会遮蔽 `AGENTS.md`；Claude 按版本、祖先 `CLAUDE.md` / `CLAUDE.local.md` 与 Project instructions 设置判断。可按用户明确要求编辑目标文件，但不自动改名、加引用或声称当前 Harness 会加载它。
- 其他 Harness 为 `BLOCKED / UNSUPPORTED AGENT`。若用户仅明确要求编辑 `AGENTS.md`，但 Codex / Claude Code 的加载状态未知，可完成文件编辑并报告 `LOADING UNKNOWN`；若用户要求让当前 Harness 确实遵循它，先问是否授权添加项目内引用/入口。

## 报告

简述修改结果与目标路径；无变化时说明 `UNCHANGED`。项目 Plugin 分别报告“文件已准备 / 注册配置已保存 / 开关配置已保存 / 实际加载已确认或未验证”；catalog 条目写入不等于客户端已发现，未完成阶段如实说明。这些聊天状态不改变编辑器的 JSON 契约。无冲突无需展开预检，轻微差异简述。不确定的来源或加载状态写 `UNKNOWN` / `LOADING UNKNOWN`，检查不完整写 `PARTIAL`。只检查时使用 [分级输出](references/conflicts.md)，不输出编辑成功。

首次写入前被阻止时报告 `BLOCKED`、原因、目标及 `Changes applied: NONE`。已完成文件准备后安装/加载受限时，列出实际已改路径与未完成阶段，不写零修改。实质冲突给出双方证据、共同条件、影响和最小方案；其他错误只给直接相关证据。失败恢复遇到并发修改时列出可能已改路径与 `UNKNOWN; CHECK PROJECT FILES`。配置编辑器的结构化报告契约保持不变，聊天无需逐字段复述。
