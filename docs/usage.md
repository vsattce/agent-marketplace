# 使用手册

[返回首页](../README.md) · [维护指南](maintenance.md)

已经安装并启用 Marketplace 的用户，从日常调用开始；安装步骤用于首次安装、换电脑或更新副本。

当前支持 Codex、Claude Code、Antigravity CLI（agy）与 DeepSeek Harness 桌面版（dsh）。安装与作用域边界分别见 [agy 说明](#antigravity-cliagy)和 [dsh 桌面版说明](#deepseek-harness-桌面版dsh)。

产品目录共有 **6 个 Plugin**，Codex **31 个 Skills**，Claude Code / agy / dsh 各 **30 个**；第三方共 26 项。personal-dev 仅保留 3 项。数量不代表当前会话已加载。

## 日常调用

在聊天中写明 Skill 和要完成的任务：

| 客户端 | 调用格式 | 示例 |
| --- | --- | --- |
| Codex | `$<plugin>:<skill>` | `$software-dev:vue 帮我实现这个组件` |
| Claude Code | `/<plugin>:<skill>` | `/software-dev:vue 帮我实现这个组件` |
| agy | `/<skill>`（以实际命令清单为准） | `/vue 帮我实现这个组件` |
| dsh 桌面版 | `/<skill>`（在 `/` 建议菜单选择或直接输入） | `/vue 帮我实现这个组件` |

可用入口以当前会话实际显示的清单为准。Skill 改名发布后，刷新客户端安装副本并开启新会话或重载 Plugin；旧完整调用名不作为别名保留。

**仅手动调用**：`setup-matt-pocock-skills`、`handoff`、`grill-with-docs`、`improve-codebase-architecture`、`to-spec`、`to-tickets`、`implement`、`implement-spec`、`retro`、`agent-manager` 和 `personal-dev` 中的 Skills。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

例如在 Codex 中：

```text
$matt:handoff 整理当前进度，供新会话继续
$agent-manager:am-context
$agent-manager:am-config 只检查当前项目与全局规则的冲突，不修改
$agent-manager:am-config 将项目 AGENTS.md 中“完成后提交并推送”改为“只提交、不推送”
```

## Skill 速查

| Plugin | Skill | 用途 | 调用方式 |
| --- | --- | --- | --- |
| matt | setup-matt-pocock-skills | 首次使用 Matt Pocock 工程 Skills 前，配置项目的问题跟踪方式、分诊标签与领域文档布局 | 用户主动（仅手动） |
| matt | handoff | 整理进度、决定和后续工作，供新会话接续 | 仅手动 |
| matt | diagnosing-bugs | 排查复杂 Bug、报错、故障和性能回归 | 任务匹配 / 手动 |
| matt | codebase-design | 使用深模块原则设计接口、确定可替换与可测试的边界 | 任务匹配 / 手动 |
| matt | grill-with-docs | 推敲方案或设计，并随讨论记录 ADR 与领域词汇 | 用户主动（仅手动） |
| matt | improve-codebase-architecture | 扫描架构改进机会，生成 HTML 报告后推敲选定方案 | 用户主动（仅手动） |
| matt | grilling | 逐轮提问以检验计划、决定或想法 | 依赖调用 / 上游任务匹配 / 手动 |
| matt | domain-modeling | 澄清领域术语，维护 GLOSSARY.md 与 ADR | 依赖调用 / 上游任务匹配 / 手动 |
| matt | tdd | 先确认测试边界，再逐项执行失败测试与最小实现的循环 | 任务匹配 / 手动 |
| matt | research | 从可信来源收集资料和 API 文档，形成研究记录 | 任务匹配 / 手动 |
| matt | writing-for-agents | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 | 任务匹配 / 手动 |
| matt | to-spec | 将已有讨论整理为 Spec | 仅手动 |
| matt | to-tickets | 大型需求拆成有阻塞关系的 Ticket | 仅手动 |
| matt | implement | 普通开发默认入口，按需 TDD，完成后 code-review | 仅手动 |
| matt | implement-spec | 大型多 Ticket 并行开发 | 仅手动 |
| matt | code-review | Standards / Spec 两轴代码审查 | 任务匹配 / 主链调用 / 手动 |
| matt | retro | 复盘 Agent 环境、工具与 token 浪费 | 仅手动 |
| common-workflow | find-skills | 按需求查找 Skill，了解能力与安装方式 | 任务匹配 / 手动 |
| software-dev | frontend-design | 指导新页面或改版的视觉风格、排版和细节 | 任务匹配 / 手动 |
| software-dev | web-design-guidelines | 审查 Web 界面、可访问性和交互规范 | 任务匹配 / 手动 |
| software-dev | vue | 基于 Vue 官方文档介绍 Vue 3 核心 API；项目级规则优先，例如项目规定使用 JavaScript 时遵循项目配置 | 任务匹配 / 手动 |
| software-dev | fastapi | 指导 FastAPI 应用与 API 开发实践 | 任务匹配 / 手动 |
| software-dev | java-springboot | 指导 Spring Boot 的 REST API、数据访问、安全认证与测试 | 任务匹配 / 手动 |
| engineering-tools | docker-build-strategies | 指导 Docker 镜像构建与缓存策略 | 任务匹配 / 手动 |
| engineering-tools | docker-compose-patterns | 指导 Compose 服务依赖、健康检查、卷、网络与开发覆盖配置 | 任务匹配 / 手动 |
| engineering-tools | playwright-cli | 通过 Playwright CLI 操作浏览器并验证交互 | 任务匹配 / 手动 |
| agent-manager | am-context | 粗略估算本轮当前仍可见的上下文；仅 Codex | 仅手动 |
| agent-manager | am-config | 检查相关冲突后编辑项目指令、安装指定 Skill 或修改受支持的 Plugin 开关；也可只读查冲突 | 仅手动 |
| personal-dev | dev-review | 只读审查当前项目或明确范围，独立复核高等级发现并生成报告；各端使用各自 adapter | 仅手动 |
| personal-dev | dev-simplify | 默认只读提出行为等价的精简建议，确认后再编辑 | 仅手动 |
| personal-dev | dev-runtime-check | 使用当前 Harness 原生 Shell / SSH 对指定远端主机、容器或服务取证；默认只读 | 仅手动 |

`grill-with-docs` 调用 `grilling` + `domain-modeling`；`improve-codebase-architecture` 调用 `codebase-design` + `grilling` + `domain-modeling`。这些依赖全部在同一 Plugin，安装 `common-workflow` 即包含完整目录和资源。`grill-me` 仅调用 `grilling`。三个入口保留上游的 `disable-model-invocation: true` 与 `allow_implicit_invocation: false`；依赖保留上游可由模型调用的策略与描述，不额外限制其触发条件。

`setup-matt-pocock-skills` 同样保留上游仅手动调用策略，用于初始化目标项目的工程 Skill 配置；先检查现状并确认草稿，再写入问题跟踪与领域文档约定。仅在目标项目已安装 `triage` 时配置分诊标签。安装此 Skill 不会自动运行初始化；执行时遵守目标项目规则，例如本仓库的 `CLAUDE.md` 仅导入 `AGENTS.md`。

`java-spring-boot` 已替换为 GitHub `awesome-copilot` 的 `java-springboot`，调用名同步改为 `$software-dev:java-springboot` / `/software-dev:java-springboot`。

`webapp-testing` 与 `dev-yagni` 已移除：网页操作与验证可使用 `playwright-cli`；长期维护 Playwright 测试时，可将专用测试规范配置在对应项目中，普通开发直接按项目规则执行。

委派开发以文件形式的 SPEC / PLAN 为输入；单任务也保存，交接保持简短。普通少量串行任务不额外建 ledger 或长报告；仅并行调度、复杂依赖、长时恢复或只读 PLAN 裁决需要时建立被 Git 忽略的 `.personal-dev/sdd/<task-id>/progress.md`。需求与计划默认保留，额外复杂任务记录或验收证据确需长期保存时才使用 `docs/personal-dev/tasks/<task-id>/`。其他产物的路径和边界见[任务产物位置](../plugins/personal-dev/references/artifacts.md)。

## Matt 精选工作流

首次在目标项目使用工程主链前，显式调用 `$matt:setup-matt-pocock-skills`（Claude：`/matt:setup-matt-pocock-skills`），配置 issue tracker 与领域文档。整个目录含 GitHub / GitLab / 本地 Markdown tracker、domain 与 triage 模板；未安装 triage 时，上游 setup 跳过其标签配置，不需要引入 triage Skill。

| 场景 | 推荐入口 |
| --- | --- |
| 需求澄清 | `$matt:grill-with-docs` |
| 需求整理 | `$matt:to-spec` |
| 大型需求拆分 | `$matt:to-tickets` |
| 普通开发（默认） | `$matt:implement` |
| 大型并行开发 | `$matt:implement-spec` |
| 困难 Bug | `$matt:diagnosing-bugs` |
| 代码审查 | `$matt:code-review` |
| Agent 工作环境复盘 | `$matt:retro` |

日常按 `grill-with-docs → to-spec → 按需 to-tickets → implement` 使用，不强制每次拆 Ticket。`implement-spec` 仅用于大型、多 Ticket 且适合多 Agent 并行的任务，不作为普通开发默认入口。Claude 前缀用 `/matt:`；agy / dsh 以实际发现的 `/skill-name` 为准。

运行依赖：`grill-with-docs → grilling + domain-modeling`；`implement → tdd + code-review`；`tdd → codebase-design`（接口 / seam 设计时）；`implement-spec → tdd + code-review`（消费 Spec / Ticket，需 tracker 配置）；`improve-codebase-architecture → codebase-design + grilling + domain-modeling`；`retro → writing-for-agents`。to-spec、to-tickets、code-review、implement-spec 在缺少项目配置时提示运行 setup。

`handoff` 用于换 Harness / 上下文、跨目录与交接；诊断、研究、架构改进和文档工具独立使用。`retro` 仅手动触发，不加到默认开发完成流程。清单不包含 ask-matt、grill-me、triage、wayfinder、prototype、pr、wizard、teach、to-questionnaire、wait-what 或 in-progress / misc / deprecated。模板中出现这些名称不构成运行依赖。

每个选定目录完整同步，保留上游 agents、模板及相对引用文件；没有自定义 wrapper、worker/reviewer 路由或客户端 adapter。上游 implement 自身会在完成后调用 code-review，其审查流程仍按 upstream 原文执行。

## 个人开发工具（Codex / Claude Code / agy / dsh）

仅保留 `dev-review`、`dev-simplify`、`dev-runtime-check`，全部手动调用。开发主链使用 matt。

dev-review 只需显式 `reviewer=<model>:<effort>`，支持 `review / r / check`、空白分隔和模型 / effort 归一化，例如 `$personal-dev:dev-review r 6.1terra high`。可选 worker 保持校验兼容，但不会派发执行代理。必须唯一匹配当前 Harness 实际模型并能显式落实 effort；不支持时 BLOCKED，不 fallback。校验器完整随 dev-review 打包，见[模型契约](../plugins/personal-dev/references/subagent-models.md)。

验证与清理遵守[命令与资源契约](../plugins/personal-dev/references/execution-resources.md)，跟踪后台 ID 至真实退出；共享 Harness 文件仅服务保留的审查能力。

### 精简当前改动

调用 `dev-simplify` 后默认由当前模型只读检查并提出行为等价的精简建议，等待确认后编辑；用户明确要求直接精简时执行。默认范围是当前项目工作区的暂存、未暂存和新增源码；用户只写 Skill 名称时仍先检查该 diff。只有 Git 不可用或没有 diff、且未指定范围时才询问，不猜最近提交或扩大到全项目。Bug 单独报告，修复需另行明确授权。

该 Skill 只作用于当前调用指向的项目和任务，不跨项目、不修改全局配置；任务结束或用户明确更换任务后不继续生效。`dev-simplify` 默认不自行派生代理或调用其他 Skill；只执行用户明确授权的精简范围。

调用 Skill 本身不扩大 Git、依赖或发布权限；这些操作按目标项目规则和当前任务已有授权处理。若组合使用两个 Skill，Codex CLI `0.162.0-alpha.17.2` 实测同一消息内的两个显式入口都会加载；Claude Code `2.1.296` 同一消息只直接加载第一个入口。Claude Code 上请在后续消息中再显式调用另一个 Skill；不要把同消息并列调用当作双入口均已加载的保证。

Codex / Claude / agy 按各自 Plugin 入口加载，dsh 通过桌面版 Skill provider 加载。安装后新建对应客户端会话确认入口；仓库有文件或已经推送，不代表当前会话已注入新 Skill。该 Skill 执行时按目标项目授权与规则处理 Git，不自动取得全局修改或发布权限。

### 增强代码审查

`$personal-dev:dev-review` / `/personal-dev:dev-review` 仅在用户显式调用时运行，例如 `$personal-dev:dev-review reviewer=6.1-terra:high`，也支持 `review / r / check`；只必填 reviewer，校验完成后才派发审查或输出报告。默认路径为 `reviewer → 主模型核验证据 → 输出报告`，小范围或普通审查只派一个 reviewer。只有有依据的 P0/P1 候选或实质争议，才再派第二个独立 reviewer 定向复核；多 reviewer 并行仅在大范围可独立分工且确有收益时启用。审查与复核共用 reviewer。默认范围仍为当前项目全部自有代码，包括存量和工作区源码，即使无 diff；指定范围时严格限定，不依赖 Git，也不启动原生 `/review`。

主模型派发前一次性核对项目规则、范围、源码可读性、基线与当前 Harness adapter；仅要求保存时核对报告位置。Codex 核对 reviewer、工具名单与强度及解释器；Claude 核对原生 Agent 与非 fork 子代理；agy 核对 invoke_subagent、独立上下文与结果读取；dsh 核对 spawn、干净上下文与完成通知。各端均核验已提供配置及实际覆写能力，不依赖主模型身份。缺少必需项时集中输出 `BLOCKED`；生产权限、凭证、配额或实时数据是可选证据，缺少时仍做代码层审查，相关运行结论列待验证。更重的专项验证仅在具体证据缺口影响结论或用户要求且只读条件允许时启用。

报告默认在聊天中输出完整结果，按审查规模组织内容，不强制逐维度表格或代理元数据登记，也不创建报告文件或审查目录。只有用户明确要求保存时才写入指定位置，未指定时使用项目 `docs/personal-dev/reviews/<review-id>/report.md`。保存失败时仍在聊天给出报告，说明原因并请求可写位置；明确要求的保存未完成时标为 `PARTIAL`。普通审查不建 progress，仅要求保存且长审查确需中断恢复时在报告同目录简记并接续。代码、配置和 Git 状态只读，不自动修复、提交或推送。报告区分 `COMPLETE`、`PARTIAL`、`BLOCKED` 执行状态与 P0–P3 风险等级；默认聊天输出不降低执行状态，发现问题不等于执行阻塞，没有高等级发现也不代表项目绝对安全。

### 远端运行诊断

`$personal-dev:dev-runtime-check` / `/personal-dev:dev-runtime-check` 仅在用户显式调用时运行。需要目标主机、SSH 连接方式、诊断对象和相关时间范围；信息足够时直接开始取证。默认只读并在聊天中汇报；只有用户明确要求保存时，才写入项目 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。明确要求修复后才执行授权范围内的必要操作，并遵守当前 Harness 的权限与审批。

Codex 使用其原生终端能力，Claude Code 使用原生 Bash 工具，agy / dsh 使用当前会话原生 Shell / SSH 工具。诊断直接连接用户指定目标，先确认主机与进程、服务或容器身份；连接或命令失败时停止远端结论，不改查当前工作站。连接和每条远端命令都设置有限超时，仅对适用的暂时性错误有限重试。按症状有限采样，比较速率时记录两次计数、单位和真实间隔，并区分宿主机、容器与应用。排查请求量时区分浏览器到自有后端和后端到第三方；部署时间与故障相邻只表示相关性，不单独证明因果。不得记录凭据或启动长期采集。

## Agent 管理工具

### 本轮上下文估算（Codex）

`am-context` 只在用户显式调用 `$agent-manager:am-context` 后运行，不接受参数、模式或子命令。它按当前对话仍可见的内容分类并给出宽松、取整的区间；不调用工具、Python 或 tokenizer，不读取文件、会话、项目规则或配置。压缩前不可见的内容不计入，只估算当前摘要；隐藏指令只估算类别，不复述。分项区间上下界分别相加得到可见内容合计，不能当作真实总输入、窗口占用或剩余容量。Claude Code / agy / dsh 不发现此入口。

### 编辑项目与冲突检查

`am-config` 支持 Codex、Claude Code、agy 与 dsh 桌面版，项目 Plugin 开关仅在下表列出的 Codex / Claude Code 环境验证；agy 的项目编辑与只读检查见 [agy 说明](#antigravity-cliagy)，dsh 见 [桌面版说明](#deepseek-harness-桌面版dsh)。编辑前检查本次操作相关的项目/全局规则、Skills、Plugins、重复能力及实际加载边界；默认不展开无关能力。轻微重复、措辞差异或已有明确覆盖关系，用一两句话提醒；实质互斥、会改变其他行为的歧义或权限边界问题，详细给出双方原文、位置、触发条件、影响和最小方案，未明确取舍前停止整批写入。提示简短不构成覆盖、禁用或删除其他能力的授权。

同一入口支持只读检查，例如 `$agent-manager:am-config 只检查当前项目与全局规则的冲突，不修改`。仅要求查冲突时，全程只读并在报告后结束，不调用配置编辑器，也不创建探测环境、临时或报告文件。用户未限定范围时检查当前项目适用的指令、Skills、Plugins 与相关全局来源；指定范围时按范围检查。来源或加载状态不明标记 `UNKNOWN`，检查不完整标记 `PARTIAL`，不能声称完整无冲突。旧的独立冲突/更新入口已移除。

修改 Plugin 开关时，逐项指定完整 Plugin 身份及启用 / 禁用状态，例如：

```text
$agent-manager:am-config 在当前项目禁用 software-dev@agent-marketplace，启用 engineering-tools@agent-marketplace
```

Claude 使用 `/agent-manager:am-config`。编辑分支只处理用户明确指定的项目操作：编辑 `AGENTS.md`、从准确来源安装 standalone Skill、准备注册项目 Plugin 与保存对应项目开关，或执行已安装 Plugin 的受支持开关。全局与项目外始终只读，不推荐组合、不提交或推送用户项目。更新安装副本仍使用下方[安装与更新](#安装与更新)步骤，维护仓库仍按[维护指南](maintenance.md#升级第三方-skill)同步。

#### 项目开关支持范围

以下版本与平台范围仅针对已安装 Plugin 的开关编辑器，不是项目文件准备或客户端能力的上限：

| 客户端与已验证版本 | 平台 | 项目 Plugin 开关 | 写入位置 |
| --- | --- | --- | --- |
| Codex `0.162.0-alpha.17.2`、`0.162.0-alpha.2` | Windows | 已安装的本地 Marketplace Plugin | `.codex/config.toml` |
| Claude Code `2.1.291`、`2.1.296` | Windows | 已安装的 Marketplace Plugin | `.claude/settings.json` |

Plugin 开关编辑器在其他操作系统返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`；这不限制 `AGENTS.md` 编辑、standalone Skill 或 Plugin 文件准备。Codex 与 Claude Code 的**单个 Skill 项目开关均不支持**。agy / dsh 的项目 Plugin 开关返回 `BLOCKED / PROJECT PLUGIN SCOPE UNVERIFIED`，不套用上述编辑器。其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。未验证的 Codex / Claude 版本、目标缺失或歧义、配置损坏、有效项目层证据不足，以及 Codex 未受信任项目或 workspace-managed Plugin，均拒绝整批操作。Claude 的 `.claude/settings.local.json` 若对目标存在反向覆盖，也会整批拒绝。

standalone Skill 的项目安装与 Skill 开关不同：用户须指定准确来源和项目内目标，并通过当前 Harness 的加载目录、来源、重复、冲突及路径检查。项目发现目录分别为 Codex / agy `.agents/skills/`、Claude Code `.claude/skills/` 及 dsh `.dsh/skills/`；dsh 也会读取项目 `.agents/skills/`，先检查同名与重复。复制所需资源并记录来源，不运行来源脚本或可能写用户 cache 的安装器。

项目 Plugin 分阶段处理：核对完整来源和项目路径，准备插件资源、项目 catalog / 当前客户端已核实的发现入口及对应开关，再验证实际发现、安装与加载。未安装不再直接阻止合法文件准备；新准备 Plugin 的文件和开关用文件工具编辑，不伪造 `installed=true` 或套用已安装开关编辑器。目录和开关保存不等于实际启用。

加载证据不足时，可在项目临时目录建立独立 `CODEX_HOME` / `CLAUDE_CONFIG_DIR`，限定配置、缓存、receipt 和日志的写入范围，不调用真实模型、不改变日常用户配置。当前 Codex CLI 的隔离实验表明，仅项目目录、catalog 和 `enabled=true` 不会自动加载该插件；因此分别报告“文件已准备 / 注册配置已保存 / 开关配置已保存 / 实际加载已确认或未验证”，catalog 条目写入不等于客户端已发现。原生安装需额外写用户记录时说明具体限制，不自动转成全局安装、关闭再项目启用的方案。旧 Skills 仅在替代入口实际加载已确认后按迁移授权移除。

`AGENTS.md` 默认编辑项目 Git/workspace 根文件；只有明确指定时才处理子目录。先核实当前 Harness 的真实指令链和遮蔽关系：Codex 同目录 `AGENTS.override.md` 优先；Claude Code v2.1.277+ 按祖先 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`、版本与 Project instructions 设置选择是否加载。用户指定编辑文件时可以改文件本身，但不会自动添加引用或声称当前会话已加载。

未决实质冲突、身份歧义或写入边界不明时停止相关批次。实际加载未知不阻止已明确授权且来源、路径和格式已确认的项目内准备，但不能报告实际启用完成。全局与项目外始终只读；保存后新会话或重新加载才能确认会话状态。详细边界见 [项目文件预检](../plugins/agent-manager/skills/am-config/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/am-config/references/codex-support.md) 与 [Claude](../plugins/agent-manager/skills/am-config/references/claude-support.md)。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Antigravity CLI（agy）

agy 产品目录包含六个 Plugin、28 个 Skills（加载机制已在 agy 1.4.2 验证）；`am-context` 仍仅 Codex。同步使用本仓库项目 Skill：Codex `$sync-agy`，Claude Code / agy `/sync-agy`。它只服务仓库维护，不进入产品目录或全局 Skills。

在仓库根也可直接运行 PowerShell 7 脚本：

```powershell
# 只读检查，不安装
pwsh -NoProfile -File .agents/skills/sync-agy/scripts/sync.ps1 -CheckOnly
# 安装或刷新当前工作区的全部产品插件到 agy 全局
pwsh -NoProfile -File .agents/skills/sync-agy/scripts/sync.ps1
```

脚本使用原生 `agy plugin validate / install / list`；默认从 PATH 查找，Windows 可回退到 `%LOCALAPPDATA%/agy/bin/agy.exe`，也可显式传 `-AgyPath`。它不执行 Git pull、不改其他客户端配置，保留其他来源的插件与已有禁用状态。仓库内容更新后重复同步即可刷新安装副本；不是实时同步。安装路径以 `agy plugin list --json` 返回值为准，本机 1.4.2 实际使用 `~/.gemini/config/plugins/`，不硬编码旧文档路径。

安装后开启新 agy 会话或按客户端提供的入口重载，确认 `/vue`、`/am-config`、`/implement`、`/retro` 等命令。手动 Skills 仍需明确调用；不要仅凭 frontmatter 声称客户端已强制门控。静态校验、安装清单及资源一致性不代表已运行真实模型、SSH 或子代理业务流程。

`personal-dev` 的审查使用 [agy 原生适配](../plugins/personal-dev/references/agy.md)，显式 reviewer、模型或 effort 覆写能力缺失时中断；精简与远端诊断沿用共享流程。`am-config` 项目编辑与只读检查范围保持不变。

### DeepSeek Harness 桌面版（dsh）

桌面版通过自带的文件系统 Skill provider 加载六个产品包的共享 Skills 与完整资源，`am-context` 仅 Codex。同步不按版本号拦截，但会使用已安装桌面版的原生加载器校验实际兼容性。项目同步入口为 Codex `$sync-dsh`、Claude Code / agy `/sync-dsh`，不进入产品目录。这里使用已安装的桌面版，无需 npm CLI。

在仓库根按项目规则核验 `mise current`、`python --version`（3.12+）及 uv，再运行；`--desktop-path` 使用实际安装路径：

```powershell
# 只读预检
uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe" --check-only
# 同步或刷新
uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe"
```

脚本复用已有 PyYAML 6.x，通过 uv 隔离安装；不修改项目依赖或系统运行时。默认数据根是 `DSH_HOME` 或 `~/.dsh`，可用 `--dsh-home` 指定。必须先启动过桌面版以初始化 `profiles/desktop`。

内容放入 `~/.dsh/marketplaces/agent-marketplace/releases/<摘要>/plugins/`，保留包内相对路径、许可证及手动调用策略；`profiles/desktop/cordis.patch.yml` 仅维护带标记的 `agent-marketplace-skills` provider。已有设置、第三方扩展和默认 Skills 根保留，旧内容快照保留；用户同名 Skills、手改快照或并发配置修改会阻止覆盖。每次同步是显式刷新，不做后台自动同步，也不注册六个 npm 扩展。

同步后重开桌面版，在 `/` 建议菜单确认 `/vue`、`/am-config`、`/implement`、`/retro` 等入口。`disable-model-invocation: true` 的 Skills 只通过用户直接输入 `/name` 注入。隔离验证会使用桌面版真实 provider 读取清单和正文，但不启动 Host 或模型，因此当前会话注入、SSH 和子代理业务执行仍需分别验证。

自有审查流程见 [dsh 审查适配](../plugins/personal-dev/references/dsh.md)和 [dsh 项目编辑适配](../plugins/agent-manager/references/dsh.md)。dev-review 要求实际提供 spawn 干净子代理；只有 fork 或能力缺失时明确 BLOCKED。`am-config` 支持项目指令编辑、standalone Skill、产品文件准备和只读检查；仅项目作用域的原生 Plugin 安装 / 开关尚未验证，不操作用户 desktop profile 代替。

### Codex

从 Gitee 添加 Marketplace，再安装需要的分类；下面列出 Marketplace 中的六个 Plugin，可按需选择：

```powershell
codex plugin marketplace add git@gitee.com:vsattce/agent-marketplace.git --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add matt@agent-marketplace --json
codex plugin add software-dev@agent-marketplace --json
codex plugin add engineering-tools@agent-marketplace --json
codex plugin add agent-manager@agent-marketplace --json
codex plugin add personal-dev@agent-marketplace --json
```

安装后默认启用，可在 UI 中单独启用或禁用整个分类。新建聊天加载入口；界面未刷新时重开客户端。

本地开发可用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。用 `codex plugin marketplace list` 核对注册，`codex plugin list --marketplace agent-marketplace --available --json` 查看可安装入口；切换同名市场来源前先核对旧注册。

**刷新**：本地来源同步后，重新执行对应的 `codex plugin add <plugin>@agent-marketplace --json`。Gitee 来源先执行 `codex plugin marketplace upgrade agent-marketplace` 刷新客户端中的 Marketplace 快照，再重新安装对应 Plugin，最后新建聊天。

### Claude Code

从 Gitee 添加并按需安装分类：

```powershell
claude plugin marketplace add git@gitee.com:vsattce/agent-marketplace.git
claude plugin install common-workflow@agent-marketplace
claude plugin install matt@agent-marketplace
claude plugin install software-dev@agent-marketplace
claude plugin install engineering-tools@agent-marketplace
claude plugin install agent-manager@agent-marketplace
claude plugin install personal-dev@agent-marketplace
```

安装默认 user scope；仅某个项目需要时，使用 `claude plugin install <plugin>@agent-marketplace --scope project`。可用 `claude plugin list --json` 或 `claude plugin details <plugin>` 查看安装信息。

本地开发使用 `claude plugin marketplace add E:\WorkSpace\agent-marketplace`。当前已验证版本的本地目录来源直接加载源目录，编辑后新建会话或执行 `/reload-plugins`。

**刷新 Gitee 来源**：先更新市场，再更新需要的 Plugin，例如：

```powershell
claude plugin marketplace update agent-marketplace
claude plugin update software-dev@agent-marketplace
```

其他分类同理，完成后新建会话。切换同名市场来源前先核对注册；移除 Marketplace 会同时卸载其插件。

**从旧开发 Plugin 迁移**：刷新 Marketplace 本身不会移除已安装的 `frontend-dev` 或 `backend-dev` 副本。先安装 `software-dev@agent-marketplace`，确认新入口可用后，再用客户端原生流程分别禁用或卸载旧 Plugin；不要手动编辑全局配置或安装缓存。Codex 可运行 `codex plugin remove frontend-dev@agent-marketplace` 与 `codex plugin remove backend-dev@agent-marketplace`；Claude Code 可运行 `claude plugin uninstall frontend-dev@agent-marketplace` 与 `claude plugin uninstall backend-dev@agent-marketplace`。新入口示例：Codex `$software-dev:fastapi`、Claude Code `/software-dev:fastapi`。

**Playwright Plugin 迁移**：`testing-automation` 已并入 `engineering-tools`。刷新 Marketplace 不会卸载旧副本；已安装旧包时，先用客户端原生流程卸载，再安装或刷新 `engineering-tools@agent-marketplace`，避免重复发现 `playwright-cli`。Codex 使用 `codex plugin remove testing-automation@agent-marketplace`；Claude Code 使用 `claude plugin uninstall testing-automation@agent-marketplace`（项目或 local 安装需选择原作用域）。新调用为 Codex `$engineering-tools:playwright-cli`、Claude Code `/engineering-tools:playwright-cli`，任务匹配策略与上游内容不变。agy 同步前也须通过原生 CLI 卸载旧包，脚本检测到旧包会在写入前停止；同步后仍用 `/playwright-cli`。dsh 重新执行 `$sync-dsh` 后，现有 provider 切换到新快照中的六个产品目录，旧快照保留，仍用 `/playwright-cli`。本仓库变更不会自动迁移日常客户端安装。

**Matt 迁移**：先安装 matt，再刷新 common-workflow 和 personal-dev，重载或新建聊天，确认旧 common-workflow Matt 副本不再被发现。Matt 调用前缀改为 `$matt:` / `/matt:`，common-workflow 仅留 find-skills。仓库迁移不自动刷新日常全局安装；agy / dsh 仍通过各自现有显式同步入口刷新完整产品目录。

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 仓库已更新，客户端仍是旧内容 | 按对应客户端刷新安装副本，再新建会话 |
| 已安装，但当前聊天找不到入口 | 核对启用状态和当前会话清单，重新加载或新建聊天；磁盘存在不等于会话可用 |
| 不知道 Skill 是否自动执行 | 仅手动调用的入口见[日常调用](#日常调用)；其他入口可按任务匹配，启用不会自行执行 |
| 配置开关返回 BLOCKED | 查看具体原因及上方支持范围；安装成功不代表具备所有项目配置能力 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)。
