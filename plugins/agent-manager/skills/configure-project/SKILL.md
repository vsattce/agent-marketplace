---
name: configure-project
description: Execute explicit Skill or Plugin enable/disable requests in the current project's Agent configuration. Only use when explicitly invoked by the user. Codex only; unsupported capabilities are BLOCKED.
---

# 配置当前项目的 Agent Skill / Plugin

纯执行型配置编辑器。只有用户明确调用 `$agent-manager:configure-project`（或当前客户端支持的显式别名）后才执行。普通聊天、技术栈识别、配置问题或冲突发现均不能触发，也不能从 resolve-conflicts 自动转入本入口。

最高边界：**当前项目内可写；用户/全局及项目外永远只读**。只接受用户逐项指定的 Skill / Plugin 开关；不推荐组合、不按项目技术栈决定、不安装缺失目标、不刷新 Marketplace、不运行 sync.py。运行本 Skill 不 commit / push 用户项目。

## 执行

1. 确认当前 Harness，而非模型品牌。本版只支持 Codex；其他 Agent 输出 `BLOCKED / UNSUPPORTED AGENT`。通过 `git rev-parse --show-toplevel` 确认当前 worktree 根；失败输出 `BLOCKED / PROJECT ROOT NOT FOUND`。不 git init、不猜目录。当前项目由调用环境确定，不能切到另一个项目完成请求。
2. 解析用户明确指定的全部 ENABLE / DISABLE 请求，保持完整批次。只接受项目范围；用户要求改全局、其他项目或 model / reasoning / MCP / sandbox / approval / profiles 等内容时整批 BLOCKED。说明具体不受支持项，不执行剩余项。
3. 使用现有会话的权威清单、已存在的安装 receipt / 有效配置和真实路径，建立**完整的当前目标清单**，包括已禁用入口、同名不同来源和项目/用户/Plugin 的目标。只读取已知 Agent 来源目录，不遍历用户内容。按 Plugin 的 `plugin-name@marketplace-name`、Skill 的真实 `SKILL.md` 路径和所属 Plugin identity 标识；所有匹配候选保留，不能按层级、第一项或近似名称挑选。无匹配 `TARGET NOT FOUND`；多个匹配 `AMBIGUOUS TARGET`，列出候选并等待用户明确身份。
4. 核对当前能力与项目配置层：读取 [Codex 能力与证据](references/codex-support.md)。必须证明项目已受信任、根 `.codex/config.toml` 会被加载，并且没有更深项目层、profile、CLI override 或 managed 限制阻止本次开关生效；否则 `CODEX PROJECT-LEVEL CONFIGURATION NOT SUPPORTED`。不改 trust 或任何其他配置来消除限制。不启动 Codex / app-server 探测，不调用可能写缓存的 plugin list / install / refresh；现有证据不足就 BLOCKED。
5. 将全部明确请求及只读证据组成 [编辑器输入](references/editor-input.md)，通过 stdin 交给 `scripts/configure_project.py`。运行目录始终是当前项目；`--cwd` 只用于传入同一项目已确认的当前目录。使用已准备好的、符合 mise / 项目约束的 Agent Python 3.12+ 环境和 tomlkit 0.13.3+（<1），以 `python -B <skill-absolute-path>/scripts/configure_project.py` 执行。依赖缺失就 BLOCKED，不为运行本 Skill 写用户目录、安装依赖或改目标项目的环境/依赖文件。避免 shell profile、运行时缓存和 bytecode 的项目外写入。
6. 编辑器完成全批定位、能力校验、canonical 路径校验、TOML 可逆解析和完整计划后，才增量写根 `.codex/config.toml`。只改变目标 Plugin 的 enabled；保留其他配置、Skill 条目、未知字段、注释和排版。缺文件只创建本次开关所需的最小合法内容；锁和 staging 也只在同一项目内，执行后清理。不人工兜底改全局配置或硬改损坏 TOML。
7. 写入后重新读取，核对所有请求状态、未请求状态及无关内容。失败尽可能恢复原始字节/删除本次新配置；并发修改阻止恢复时明确报告，不能宣称零修改或成功。项目外读取目标/配置始终只读。返回完整结果；启动新会话或重新加载受信任项目才能获得新的会话状态，不将持久化验证声称为当前会话热重载。

## 本版能力

- 已安装的本地 Marketplace Plugin：Codex 项目级 ENABLE / DISABLE，可批量事务执行。
- 单个 Skill：`BLOCKED / CODEX PROJECT-LEVEL CONFIGURATION NOT SUPPORTED`。本机 0.162.0-alpha.2 会读取项目 `skills.config`，但加载器只应用用户层的 Skill 开关；不写无效的项目条目，不改用户配置兜底。
- workspace-managed / 无可靠本地身份 / 未安装 Plugin：BLOCKED；Marketplace 可发现、磁盘缓存存在不等于已安装。
- 未验证的 Codex 版本：BLOCKED，维护者需先补充隔离加载器证据。本 Skill 执行时不能自行探测或升级客户端。

含一个不受支持目标的混合批次，整个操作为 BLOCKED，零配置写入。

## 报告

成功：`SUCCESS`、Agent、Project、Config、实际 Changed（ENABLE / DISABLE + 完整身份）、Unchanged、`Global files modified: NONE`，说明已重读项目配置及激活边界。

失败：`BLOCKED`、Reason、Target（适用时）、Matches（歧义时）、`Changes applied: NONE`、`Global files modified: NONE`。验证后恢复失败/外部并发改动时，Changes applied 改为 `UNKNOWN; CHECK PROJECT CONFIG`，并给出原因，不展示完整配置或敏感值。
