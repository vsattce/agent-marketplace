---
name: resolve-conflicts
description: "Resolve duplicate Agent Plugin / Skill entries within the current project. Only use when explicitly invoked by the user."
---

# 整理当前项目的 Agent 冲突

只在用户以 `$resolve-conflicts` 或 `$agent-manager:resolve-conflicts` 明确选择本 Skill 时执行。讨论 Plugin、发现配置或另一个 Skill 提到本 Skill，都不构成调用。

## 识别与扫描

1. 首先确认当前工作目录属于真实项目：Git 根目录，或向上找到的 Agent 项目配置、package / build 文件。使用 `scripts/project_config.py` 的项目识别规则辅助判断；它支持项目内部目录。用户 home、Agent 用户配置目录及普通空目录不是项目。无法识别时立即输出「该 Skill 只能在项目目录中执行。」并停止，零修改。
2. 从当前会话 Harness 身份识别 Agent；安装了 `codex` 不代表当前 Agent 是 Codex。身份不明输出 `BLOCKED` 和原因；非 Codex 输出 `UNSUPPORTED AGENT`，停止。Codex 时读取 [Codex adapter](../../references/codex.md)，完成当前官方规范、配置层级、控制粒度、信任和实际加载状态的核验。关键证据缺失即停止修改。
3. 扫描实际有效 Skills：当前会话/官方 `skills/list` 的名字、namespace、description、绝对入口路径、enabled 状态；Plugin list 的来源、项目/用户 scope；项目与用户 Marketplace、standalone 目录和有效配置。沿项目根到 cwd 的配置层次检查。文件安装、缓存存在、Marketplace 收录与实际启用分别记录，不能把缓存或未安装入口算作有效冲突。只读用户配置，报告时只摘取相关状态，隐藏凭据。
4. 按 frontmatter 的**完全相同 Skill name**分组，namespace 分开呈现。不同名的类似功能仅标记 `POSSIBLE OVERLAP`，不自动处理。不能确定 scope 或是否实际加载的候选标记 `BLOCKED`，不推测。用户明确保留/优先/禁用的来源先于默认规则；否则项目级 > 用户/全局。同级多来源无唯一胜者时报告选择项，不自动修改。

## 计划与执行

先输出 `Current Agent`、`Project`、`Detected duplicates`，每个来源的 namespace / Plugin / scope / description，再输出 winner、reason、目标配置及 action。用户调用已授权安全的项目内处理，无需重复确认。

**优先使用 Skill 级精确 path selector，不能按 name 禁用。** 对每个需要屏蔽的 global Plugin Skill，先运行 [probe_codex.py](scripts/probe_codex.py)（原项目约束允许的 mise Python 3.12+；脚本无额外依赖）：

```text
uv run --python <mise Python 的实际路径> --no-python-downloads --script <本 Skill 路径>/scripts/probe_codex.py --global-plugin-root <官方 metadata 确认的已安装 Plugin 根> --skill <重复 Skill name> --project-skill <项目同名 Skill 目录>
```

探测在临时 CODEX_HOME、临时 Git 项目和复制的 Plugin 内运行本机 Codex，不运行模型/Skill 流程、不写真实项目或用户配置。比较项目层精确 SKILL.md 路径与目录路径两种 selector，并确认：目标 global Skill 从**可用 enabled 列表**消失、项目同名 Skill 保留、Plugin 其他 Skill 保留、没有 Plugin disable、用户层未改。另在临时用户配置做对照，区分项目过滤缺陷与 selector 无效。只有 `SUPPORTED` 且全部检查通过，才使用报告确认的路径格式编辑真实项目配置；selector 永远重新取自真实 `skills/list`，不能使用临时路径。额外组件的 Plugin 无法安全复制探测时 BLOCKED，不删除其组件做假测试。

若当前版本仅用户层 Skill disable 生效而项目层不生效，输出 `BLOCKED` 和「当前 Codex 版本虽然支持 skill-level disable，但项目级 .codex/config.toml 中的 skills.config 当前不会生效。」同时报告冲突 Skill、global 实际路径、project 实际路径、Codex 版本、失败机制，以及人工方案（升级到已验证支持的 Codex；保留现状；手动选择入口只是暂时使用方式，不能满足持久化隔离）。不写无效规则，不修改用户配置、不注入启动 `-c`、不创建 alias、不删除文件，**不 fallback 禁用整个 Plugin**。

根据 adapter 已验证的能力决定控制粒度：

- 独立 Skill：仅在项目层按准确加载路径 disable 已获本机验证时，用项目 `skills.config` 定位该入口。
- Plugin 内单个 Skill：必须先通过上述兼容性探测；只看到 schema 字段不足以证明。用户明确保留 global / 禁用 project 时同样用 project Skill 的精确加载路径，并先验证该项目层 override 能作用于它。
- 整个 Plugin：仅作为用户明确选择关闭整个 Plugin 时的极端处理，且仍先报告连带影响。自动冲突整理不使用它替代失败的项目 Skill disable。不得因一个 handoff 冲突关闭同时提供 research / diagnosing-bugs 的 Plugin。

对于不能安全处理的冲突，输出 `BLOCKED`、两个来源、可用控制粒度、连带影响和人工方案（保留现状、选择另一来源、明确同意禁用整个 Plugin）。停止**该冲突**自动修改，独立可解决项可继续。

修改只写当前项目配置，增量保留 model / reasoning / MCP / sandbox / approval / profiles / 其他 Plugin 及所有无关项。使用 [project_config.py](scripts/project_config.py)：默认只传入已获 loader 验证的精确 `skill_updates`。用户明确关闭整个 Plugin 且全部能力都在指定淘汰范围时，才可通过 `plugin_disable_update(plugin_id, installed_plugin_root, losing_skill_names)` 校验实际所有 Skill 和附加能力，再传入 `plugin_updates`。先解析并计算候选，核验仅目标字段变化，再写入并重新读取。该 helper 不判断冲突胜者；先完成上面的扫描、连带影响、官方能力和 trust 核验。直接运行脚本只识别项目并预检，**不会写入**。复杂或不支持的 TOML 结构、符号链接/目录重定向、并发变更、权限不足时停止并输出原因。

修改后重新读取目标 TOML，再通过与扫描相同的官方有效状态/Skills 发现机制验证：项目同名 Skill 仍可用、目标 global 路径不再可用、同 Plugin 其他 Skill 全部仍可用、用户配置字节未变、Plugin 未被关闭。五项全部通过才记 `RESOLVED`。若需要新会话/重启，明确 `PENDING RELOAD`；写入成功不能宣称冲突已解除。无法验证时标记 `Unresolved`，不继续扩大改动。

最后报告 `Changed`、`Unchanged`、`Resolved`、`Unresolved`。没有冲突也输出扫描范围。

禁止卸载/删除 Plugin 或 Skill、修改用户全局状态/skills、其他项目、Marketplace、sources 或 lock、第三方 Skill、安装新 Plugin、换源、commit 或 push。
