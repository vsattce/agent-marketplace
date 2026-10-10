---
name: resolve-conflicts
description: "Resolve duplicate Agent Plugin / Skill entries within the current project. Only use when explicitly invoked by the user."
---

# 整理当前项目的 Agent 冲突

只在用户以 `$resolve-conflicts` 或 `$agent-manager:resolve-conflicts` 明确选择本 Skill 时执行。讨论 Plugin、发现配置或另一个 Skill 提到本 Skill，都不构成调用。

## 最高优先级：项目外绝不写入

全局范围 = READ ONLY；当前项目范围 = READ / WRITE；项目外任何内容 = NEVER WRITE。此边界高于解决冲突的目标，也不因用户指定胜者而放宽。

先固定调用时 cwd 和可靠识别的 projectRoot，不切换 cwd 或用另一个项目路径扩大范围。只有当前项目根目录及其子目录可写。每次写入、创建、覆盖、patch、删除、重命名、移动、临时文件及失败清理前，检查 target 的 absolute/realpath 与 projectRoot 的 canonical path；使用平台感知的路径包含关系，不能字符串前缀匹配。处理 `..`、相对路径、Windows 大小写/盘符；遇到 symlink、junction、hardlink 或路径重定向拒绝写入。最终落在项目外时立即输出 `BLOCKED` / `Reason: target path is outside project root`，停止该操作。

`~/.codex/*`、`~/.agents/*`、`~/.claude/*`、`~/.config/*`、实际 CODEX_HOME、用户/全局 Plugin / Skill 配置与安装状态、Marketplace 注册、全局缓存、其他项目和 workspace 全部只读。可读取清单、实际 Skill 路径、配置层及 metadata；不能写入、清理、卸载、禁用全局状态或修改 shell profile、环境。global Skill 路径作为项目 TOML 中的 selector 是只读引用，绝不编辑该路径。

边界也约束工具副作用：标注 list/read 的 CLI 或 RPC 仍可能写日志/缓存。只有证实无项目外写入才可调用；否则读取已有会话/metadata。禁止原来的系统临时目录探测、临时用户层对照、Plugin 安装和 Marketplace 注册。只设置 CODEX_HOME 或缓存环境变量不能证明子进程受限；没有已验证的项目内执行约束就 BLOCKED。运行 Python 使用 `-B` 防止写入缓存 Plugin 的 `__pycache__`；依赖必须已有，不能让 uv 自动在项目外安装/缓存。无法满足时只做读取，不运行 helper。

## 识别与扫描

1. 首先确认当前工作目录属于真实项目：优先 `git rev-parse --show-toplevel`，否则采用 Agent 确认的 workspace/project root 或向上找到的实际 Agent 项目配置、package / build 文件。使用 `scripts/project_config.py` 的项目识别规则辅助判断；它支持项目内部目录。用户 home、Agent 用户配置目录及普通空目录不是项目。无法可靠识别时输出 `BLOCKED` / `Reason: resolve-conflicts can only run inside a project directory.`（该 Skill 只能在项目目录中执行），立即停止；不猜根目录，不创建配置，不初始化 Git。
2. 从当前会话 Harness 身份识别 Agent；安装了 `codex` 不代表当前 Agent 是 Codex。身份不明输出 `BLOCKED` 和原因；非 Codex 输出 `UNSUPPORTED AGENT`，停止。Codex 时读取 [Codex adapter](../../references/codex.md)，完成当前官方规范、配置层级、控制粒度、信任和实际加载状态的核验。关键证据缺失即停止修改。
3. 扫描实际有效 Skills：当前会话/官方 `skills/list` 的名字、namespace、description、绝对入口路径、enabled 状态；Plugin list 的来源、项目/用户 scope；项目与用户 Marketplace、standalone 目录和有效配置。沿项目根到 cwd 的配置层次检查。文件安装、缓存存在、Marketplace 收录与实际启用分别记录，不能把缓存或未安装入口算作有效冲突。只读用户配置，报告时只摘取相关状态，隐藏凭据。
4. 按 frontmatter 的**完全相同 Skill name**分组，namespace 分开呈现。不同名的类似功能仅标记 `POSSIBLE OVERLAP`，不自动处理。不能确定 scope 或是否实际加载的候选标记 `BLOCKED`，不推测。用户明确保留/优先/禁用的来源先于默认规则；否则项目级 > 用户/全局。同级多来源无唯一胜者时报告选择项，不自动修改。

## 计划与执行

先输出 `Current Agent`、`Project`、`Detected duplicates`，每个来源的 namespace / Plugin / scope / description，再输出 winner、reason、目标配置及 action。用户调用已授权安全的项目内处理，无需重复确认。

**优先使用 Skill 级精确 path selector，不能按 name 禁用。** 核验当前版本、官方实现和实际项目层过滤行为。验证过程也只能写固定 projectRoot 内，不能创建项目外测试目录、修改用户配置或安装测试 Plugin。必须确认：目标 global Skill 从**可用 enabled 列表**消失、项目同名 Skill 保留、Plugin 其他 Skill 保留、没有 Plugin disable、用户层未改。仅 schema/config/read 可见不足以通过。只有当前版本的实际行为与全部安全检查通过，才使用真实 `skills/list` 的精确路径增量编辑项目配置。

[probe_codex.py](scripts/probe_codex.py) 已改为只读预检：读取当前项目与目标 Plugin Skill 文件，并报告路径；它不启动 Codex、不复制/安装 Plugin、不写临时 CODEX_HOME。缺少已验证的项目内子进程约束时返回 BLOCKED，不能据此宣称 filtering 已通过。不能获得安全的当前行为证据就停止对应修改；禁止调用仓库开发测试作为运行时 workaround。

若已确认当前版本仅用户层 Skill disable 生效而项目层不生效，输出 `BLOCKED` 和「当前 Codex 版本虽然支持 skill-level disable，但项目级 .codex/config.toml 中的 skills.config 当前不会生效。」同时报告冲突 Skill、global/project 实际路径、版本、缺少的项目级能力、为何另一办法需要全局修改，以及「红线禁止修改全局，本次不执行」。证据不够则报告无法安全验证，不能把历史缺陷当当前事实。人工方案仅保留现状或由用户升级后重新验证；手动选择入口不能满足持久化隔离。**项目级做不到就 BLOCKED，绝不 fallback 到用户配置、全局 Plugin / Skill 状态、shell alias/profile、启动 `-c`、环境、Marketplace 或全局缓存，也不禁用整个 Plugin。**

根据 adapter 已验证的能力决定控制粒度：

- 独立 Skill：仅在项目层按准确加载路径 disable 已获本机验证时，用项目 `skills.config` 定位该入口。
- Plugin 内单个 Skill：必须先通过上述兼容性探测；只看到 schema 字段不足以证明。用户明确保留 global / 禁用 project 时同样用 project Skill 的精确加载路径，并先验证该项目层 override 能作用于它。
- 整个 Plugin：仅作为用户明确选择关闭整个 Plugin 时的极端处理，且仍先报告连带影响。自动冲突整理不使用它替代失败的项目 Skill disable。不得因一个 handoff 冲突关闭同时提供 research / diagnosing-bugs 的 Plugin。

对于不能安全处理的冲突，输出 `BLOCKED`、两个来源、可用控制粒度、连带影响和人工方案（保留现状、选择另一来源、明确同意禁用整个 Plugin）。停止**该冲突**自动修改，独立可解决项可继续。

修改只写当前项目配置，增量保留 model / reasoning / MCP / sandbox / approval / profiles / 其他 Plugin 及所有无关项。使用 [project_config.py](scripts/project_config.py)：默认只传入已获 loader 验证的精确 `skill_updates`。用户明确关闭整个 Plugin 且全部能力都在指定淘汰范围时，才可通过 `plugin_disable_update(plugin_id, installed_plugin_root, losing_skill_names)` 校验实际所有 Skill 和附加能力，再传入 `plugin_updates`。先解析并计算候选，核验仅目标字段变化，再写入并重新读取。该 helper 不判断冲突胜者；先完成上面的扫描、连带影响、官方能力和 trust 核验。直接运行脚本只识别项目并预检，**不会写入**。复杂或不支持的 TOML 结构、符号链接/目录重定向、并发变更、权限不足时停止并输出原因。

修改后重新读取目标 TOML，再通过与扫描相同的官方有效状态/Skills 发现机制验证：项目同名 Skill 仍可用、目标 global 路径不再可用、同 Plugin 其他 Skill 全部仍可用、用户配置字节未变、Plugin 未被关闭。五项全部通过才记 `RESOLVED`。若需要新会话/重启，明确 `PENDING RELOAD`；写入成功不能宣称冲突已解除。无法验证时标记 `Unresolved`，不继续扩大改动。

最后报告 `Changed`、`Unchanged`、`Resolved`、`Unresolved`。没有冲突也输出扫描范围。

禁止卸载/删除 Plugin 或 Skill、修改用户全局状态/skills、其他项目、Marketplace、sources 或 lock、第三方 Skill、安装新 Plugin、换源、commit 或 push。
