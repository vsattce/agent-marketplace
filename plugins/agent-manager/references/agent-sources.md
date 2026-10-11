# 其他 Agent 的来源发现

用于冲突查找；am-update 使用独立的 Codex / Claude / Kimi adapter。只读查看当前 Agent 的已知来源，不启动新 Harness，不操作安装、刷新、禁用或配置。下面是来源示例，不是允许的 Agent 白名单，也不是固定文件名表。

## 通用发现

先确认 Harness 产品与版本，再从会话加载信息、有效配置、自定义 context/instruction 文件名和 Plugin/Extension manifest 定位全局与项目来源。模型名字不等于 Harness 身份。工具支持其他品牌模型时，仍按宿主 Agent 的规则扫描。

未列出的 Agent 也按此流程处理：优先当前会话提供的路径与加载证据；需要补充机制时查该产品官方文档，核对项目/用户/managed 层级、子目录与路径条件、引用和优先级。只有真实可用目录才查内容，不猜 `~/.<品牌>`，不遍历整个 home。别名、历史入口及兼容文件仅在有配置/加载证据时纳入。机制无法核实时继续已知文件的静态比较，相关来源/优先级写 `UNKNOWN`，报告 `PARTIAL`，不直接拒绝其他 Agent，也不套用 Codex 规则。

对于一次要求检查多个 Agent 的任务，分别建立来源与结果，跨 Agent 的文件差异仅记兼容性风险；只有它们实际被同一个 Harness 加载且条件相同才判运行冲突。默认检查当前 Harness。

## Claude Code

主要指令来源：全局 `~/.claude/CLAUDE.md`、`~/.claude/rules/`；项目 cwd 及其祖先的 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md` 与 `.claude/rules/`。跟进适用的 `@path` 引用，按 `paths` 和子目录读取条件记录作用域。项目根外祖先单列为继承来源。内容通常合并，不能照搬 Codex“每层首个文件”或假定项目规则消除所有全局要求；检查 exclusions、导入、managed 层和项目指令设置。

`CLAUDE.md` 是主要入口，但不能断言永远不读 `AGENTS.md`：当前官方文档说明较新版本可按版本、项目指令设置与 CLAUDE 文件是否存在选择加载 AGENTS.md，CLAUDE.md 也可显式导入它。执行时核对实际版本、配置和会话证据。

Skills 从会话清单、项目 `.claude/skills`、用户 `~/.claude/skills`、Plugin 或有效兼容 commands/额外路径发现。调用策略按 Claude 规范解释，`agents/openai.yaml` 不作为 Claude 启用证据。Plugin 身份、安装 scope、启用层及 hooks / agents / MCP 等能力结合 manifest、receipt 和有效 settings 核对；常见用户/项目配置为 `~/.claude/settings.json`、`.claude/settings.json`、`.claude/settings.local.json`。已有 /memory、/skills、/plugin 信息可辅助确认，不操作这些界面的修改功能。

官方依据（2026-10-10 核对）：

- [指令、rules、imports 与 AGENTS.md 兼容机制](https://code.claude.com/docs/en/memory)
- [Skills](https://code.claude.com/docs/en/skills)
- [设置来源与优先级](https://code.claude.com/docs/en/settings)

## Kimi Code

读取 [Kimi 来源与只读检查](kimi.md) 的“来源与加载证据”：确认实际数据根、项目指令链、standalone 与 Plugin Skill 路径，以及 receipt / manifest 的真实身份。根聚合和分类同时安装、同名 standalone 覆盖均作为来源重叠检查；托管副本不等于原目录，也不等于当前会话加载。

## Gemini CLI

主要指令来源：全局 `~/.gemini/GEMINI.md`、workspace/祖先与按访问触发的上下文文件。文件名可由 settings 的 `context.fileName` 自定义为单个或多个名称，因此 `GEMINI.md` 只是默认入口。检查实际导入、ignore、trust root、加载限制与当前会话的上下文证据，不把所有扫描文件当作同时生效。当前上下文指南与配置参考对发现范围的表述如有差异，以本机加载证据确认，否则标 `UNKNOWN`。

Skills 从实际会话清单、workspace `.gemini/skills`、用户 `~/.gemini/skills`、兼容 `.agents/skills` 和 Extension 提供的入口发现。Gemini 的插件能力可能称为 Extension：查看已记录安装来源、`gemini-extension.json`、启用状态及其 context 文件、Skills、MCP、hooks 等相关内容；不以 Codex Plugin 字段判断。用户 `~/.gemini/settings.json`、项目 `.gemini/settings.json` 和其他实际生效层用于核对加载条件。已有 /memory show 或 Skills/Extension 清单是证据来源，不调用 refresh/install/enable/disable 做验证。

官方依据（2026-10-10 核对）：

- [GEMINI.md 层级、自定义名称与导入](https://geminicli.com/docs/cli/gemini-md/)
- [Skill 来源与兼容目录](https://geminicli.com/docs/cli/creating-skills/)
- [Extension manifest 与上下文文件](https://geminicli.com/docs/extensions/reference/)
- [配置与上下文加载](https://geminicli.com/docs/reference/configuration/)
