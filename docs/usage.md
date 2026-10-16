# 使用手册

[返回首页](../README.md) · [维护指南](maintenance.md)

已经安装并启用 Marketplace 的用户，从日常调用开始；安装步骤用于首次安装、换电脑或更新副本。

当前支持 Codex 与 Claude Code；其他客户端暂不适配或维护。

Codex 与 Claude Code 均有 **6 个 Plugin**；Codex 共 **19 个 Skills**，Claude Code 共 **18 个**。四个第三方聚合 Plugin 收录 13 项；本仓库自有的 `agent-manager` 在 Codex / Claude Code 分别有 2 / 1 项，`personal-dev` 两端各有 4 项。第三方来源、作者与许可证边界见 [README](../README.md)。

## 日常调用

在聊天中写明 Skill 和要完成的任务：

| 客户端 | 调用格式 | 示例 |
| --- | --- | --- |
| Codex | `$<plugin>:<skill>` | `$software-dev:vue 帮我实现这个组件` |
| Claude Code | `/<plugin>:<skill>` | `/software-dev:vue 帮我实现这个组件` |

可用入口以当前会话实际显示的清单为准。Skill 改名发布后，刷新客户端安装副本并开启新会话或重载 Plugin；旧完整调用名不作为别名保留。

**仅手动调用**：`handoff`、`agent-manager` 和 `personal-dev` 中的 Skills。其他 Skill 可在任务匹配时由 Agent 选用，也可手动指定；自动选用不保证每次发生，启用 Plugin 不会自行执行任务。

例如在 Codex 中：

```text
$common-workflow:handoff 整理当前进度，供新会话继续
$agent-manager:am-context
$agent-manager:am-config 只检查当前项目与全局规则的冲突，不修改
$agent-manager:am-config 将项目 AGENTS.md 中“完成后提交并推送”改为“只提交、不推送”
```

## Skill 速查

| Plugin | Skill | 用途 | 调用方式 |
| --- | --- | --- | --- |
| common-workflow | handoff | 整理进度、决定和后续工作，供新会话接续 | 仅手动 |
| common-workflow | diagnosing-bugs | 排查复杂 Bug、报错、故障和性能回归 | 任务匹配 / 手动 |
| common-workflow | research | 从可信来源收集资料和 API 文档，形成研究记录 | 任务匹配 / 手动 |
| common-workflow | writing-for-agents | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 | 任务匹配 / 手动 |
| common-workflow | find-skills | 按需求查找 Skill，了解能力与安装方式 | 任务匹配 / 手动 |
| software-dev | frontend-design | 指导新页面或改版的视觉风格、排版和细节 | 任务匹配 / 手动 |
| software-dev | web-design-guidelines | 审查 Web 界面、可访问性和交互规范 | 任务匹配 / 手动 |
| software-dev | vue | 基于 Vue 官方文档介绍 Vue 3 核心 API；项目级规则优先，例如项目规定使用 JavaScript 时遵循项目配置 | 任务匹配 / 手动 |
| software-dev | fastapi | 指导 FastAPI 应用与 API 开发实践 | 任务匹配 / 手动 |
| software-dev | java-springboot | 指导 Spring Boot 的 REST API、数据访问、安全认证与测试 | 任务匹配 / 手动 |
| engineering-tools | docker-build-strategies | 指导 Docker 镜像构建与缓存策略 | 任务匹配 / 手动 |
| engineering-tools | docker-compose-patterns | 指导 Compose 服务依赖、健康检查、卷、网络与开发覆盖配置 | 任务匹配 / 手动 |
| testing-automation | playwright-cli | 通过 Playwright CLI 操作浏览器并验证交互 | 任务匹配 / 手动 |
| agent-manager | am-context | 粗略估算本轮当前仍可见的上下文；仅 Codex | 仅手动 |
| agent-manager | am-config | 检查相关冲突后编辑项目指令、安装指定 Skill、准备注册项目 Plugin 与配置开关；也可只读查冲突 | 仅手动 |
| personal-dev | dev-delegate | 主模型安排任务，独立编码与验收代理执行，主模型最终整体检查；Codex / Claude Code | 仅手动 |
| personal-dev | dev-review | 只读审查当前项目或明确范围，独立复核高等级发现并生成报告；Codex / Claude Code | 仅手动 |
| personal-dev | dev-simplify | 默认只读提出行为等价的精简建议，确认后再编辑 | 仅手动 |
| personal-dev | dev-runtime-check | 使用当前 Harness 原生 Shell / SSH 对指定远端主机、容器或服务取证；默认只读 | 仅手动 |

`java-spring-boot` 已替换为 GitHub `awesome-copilot` 的 `java-springboot`，调用名同步改为 `$software-dev:java-springboot` / `/software-dev:java-springboot`。

`webapp-testing` 与 `dev-yagni` 已移除：网页操作与验证可使用 `playwright-cli`；长期维护 Playwright 测试时，可将专用测试规范配置在对应项目中，普通开发直接按项目规则执行。

单个简单任务直接在交接消息中提供目标、修改范围、必要约束、验收条件、最小验证和原有改动，不额外填写多任务编排字段、建 ledger 或生成报告文件。委派开发拆成两个及以上任务（含串行依赖任务）时，自动建立被 Git 忽略的 `.agent-tmp/dev-delegate/<task-id>/progress.md`；真正需要长期保留设计、复杂任务记录或验收证据时才使用 `docs/personal-dev/tasks/<task-id>/`。其他产物的路径和边界见[任务产物位置](../plugins/personal-dev/references/artifacts.md)。

## 个人开发工具（Codex / Claude Code）

```text
$personal-dev:dev-delegate 实现当前需求，保留现有接口和范围外行为
$personal-dev:dev-delegate 实现当前需求，编码 medium，验收 xhigh
$personal-dev:dev-review 检查当前项目的性能、资源、请求、磁盘和长期运行风险
$personal-dev:dev-simplify 检查当前 diff，先提出行为等价的精简建议
$personal-dev:dev-runtime-check 检查用户指定的远端主机和服务；默认只读
```

Claude Code 使用 `/personal-dev:dev-delegate` 与 `/personal-dev:dev-review`，未指定时沿用当前子代理模型与思考配置，省略 `model` / `effort`；用户明确指定时按本轮原生工具能力核验，也不要求 Codex 的 Luna、`reasoning_effort` 或 Python 检查器。派发前显示模型策略；实际 ID 或强度无法确认时标 `UNKNOWN`，不冒充已验证值。独立验收、两轮修复上限与主模型终审流程和 Codex 相同。

主模型按可独立验收的完整功能或修复点拆任务，同类小改动合并。同一功能的 DTO、Service、Controller 与前端调用优先交给一个编码代理完成后统一验收；确有独立交付边界或规模需要时才拆开。Codex 当前已确认的低成本编码系列为 Luna：从本轮派发工具实际允许的型号中选择与主模型同一大版本内数字版本最高者，默认 `high` 编码；另一个干净上下文的同型号代理默认 `xhigh` 验收。用户可分别指定本次编码与验收强度，明确指定的值优先，未指定的角色保留默认值，无需再次确认强度；不支持的值会说明原因并中断。

多任务、复杂或高风险任务在首次派发前，对照已确认需求检查计划中的关键值、接口、上下游产出和验收 / 验证要求；没有计划文件时直接检查任务安排，不强制写文档。必要结论写入已有 ledger 或派发交接，编码和验收使用同一版要求。主模型先补齐关键设计；默认模型仍不适配时说明能力缺口，按本次已有授权和精确型号覆写规则处理，提高思考强度不等于更换更强模型。

多任务或确需进度恢复时，每项派发前明确 `task_id`、目标、`depends_on`、`write_scope` 和 `can_parallel`。拆开的依赖包括接口、数据结构和调用链，前项的产出是后项输入时顺序执行；前项独立验收通过、契约确定后才启动下游。默认一个编码代理，仅在任务无依赖、写入不重叠、无变化中的共享契约、原生并发与槽位可用且合并风险低时允许两个，最多三个。范围含目录、测试和生成输出；同文件、目录包含、共享契约或不明边界均串行。共享端口、fixture 和测试输出的验证也须避免冲突，不支持安全并发时回退串行，不引入自动 worktree、merge 或 Agent Teams。

多任务 ledger 由主模型单独维护，记录任务依赖、并行决定、实际 Agent/task id、模型与强度、状态、修复轮次、基线和必要证据。恢复先读当前执行 ledger，再核对实际代码、Git 和代理状态；不重派仍在运行或已验收完成的任务。修复派发前预记本轮和 `FIXING`，修复结束进入 `REVIEW`，同轮复验不再次加一；代理重建、任务改名或 compact 不清零计数。中断和阻塞保留记录；全部验收、主模型整体检查及已授权收尾完成后才清理本次临时目录，用户要求保留时遵从。

独立验收使用区别于 Coder 的新干净上下文，仅提供需求、必要接口约束、实际改动、编码报告和验证证据，不复制完整思考或聊天。Coder 与 Reviewer 不直接交流，问题由主模型传递；验收期间冻结该范围和相关依赖的写入。独立任务可分别验收，不可分割功能单元可以合并，但每项保留独立结论与修复预算。完整契约见[任务编排与进度恢复](../plugins/personal-dev/skills/dev-delegate/references/orchestration.md)。

Codex 需要本轮可靠的主模型身份、当前派发工具允许名单和支持强度信息。6.1 / 6.2 主模型可以用 6 Luna；7 主模型不能自动回退到 6 或 5.6。信息缺失、陌生命名、版本歧义、强度不支持或工具不能覆写时输出具体原因并中断。用户明确确认精确替代型号后可用于当前任务；持久接纳新系列需另行维护，不凭升级推荐或价格猜测选模型。

编码开始前一定先显示实际结果，例如：

```text
编码模型：gpt-6-luna｜思考强度：high
验收模型：gpt-6-luna｜思考强度：xhigh
```

成功后直接执行，不额外确认是否开始。用户可明确覆写编码 / 任务验收的型号或强度；有变化先重新显示。独立验收检查需求、实现、相关调用点和验证证据，简单任务聚焦验收条件、实际差异和直接影响，阻塞问题完整汇总，风格建议不扩大返工。额外整体终审仅在用户明确要求，或改动存在具体的安全 / 权限、并发 / 事务一致性、破坏性迁移、公共接口不兼容风险时触发。普通页面、兼容接口新增和常规前后端联动由主模型整体检查；任务多或代码量大本身不增加终审代理。

终审固定使用本轮已确认的会话型号，思考强度默认比会话低一档；紧邻档不可用时只可再降低，最低档不再降低，无可用档时停止。材料充分但终审仍明确报告判断困难时，可自动升到会话当前强度一次。例如会话 `gpt-6.1-sol / high`，初次终审为同型号 `medium`，困难升级最多到 `high`，不会因工具允许而选择 `ultra`。已确认的代码缺陷走原有修复流程；缺材料、权限、业务决策或仅测试失败不触发思考升级。

Codex 在既有模型选择脚本中按需传 `final_review_required: true`、`primary_effort`、`primary_effort_source`；只有困难升级时传 `final_review_escalated: true`。使用脚本返回的 `final_review` 与展示行，编码 / 任务验收的既有调用保持兼容。Claude 按本轮原生能力核验同型号、低一档和上限，不套用 Codex 档位或参数；无法确认当前会话设置或有效控制强度时停止，不能把默认 `UNKNOWN` 当作预算满足。上限只取本轮可靠运行时信息或用户明确说明，不取默认配置或工具最高档。派发、升级和恢复前核验当前上限，展示实际设置；已有 ledger 记录触发风险、上限来源、代理、版本、结论及已用升级状态，不调用额外 Skill，不因代理重建或恢复重新获得升级次数。

主模型整合独立终审结论，并核对总需求、范围和最终代码版本；普通低风险单任务或互不关联的简单多任务保留原有轻量整体检查。已有内部验收结论有效时不重复全面审查，有具体疑点或后续改动时只检查受影响部分。初次实现后每个任务累计最多两轮修复，第二轮复验仍阻塞则全流程停止，由用户决定升级；主模型不自动接手编码。终审问题归属到相关任务，使用其剩余次数并独立复验；无法安全归属、预算耗尽或必要证据不足时停止，不通过新增终审任务重开预算。

Codex 随 Skill 提供的 Python 标准库检查器只校验主模型根据当前工具整理的模型信息，不连接服务、不验证输入来源、不修改配置，也不是原生派发工具的强制拦截器。使用已有且符合规则的 Agent 工具解释器；缺少环境时中断，不自动安装或切换。费用与 Codex 额度的实际节省需要实测，不按 API 标价推算固定比例。

### 精简当前改动

调用 `dev-simplify` 后默认由当前模型只读检查并提出行为等价的精简建议，等待确认后编辑；用户明确要求直接精简时执行。默认范围是当前项目工作区的暂存、未暂存和新增源码；用户只写 Skill 名称时仍先检查该 diff。只有 Git 不可用或没有 diff、且未指定范围时才询问，不猜最近提交或扩大到全项目。Bug 单独报告，修复需另行明确授权。

该 Skill 只作用于当前调用指向的项目和任务，不跨项目、不修改全局配置；任务结束或用户明确更换任务后不继续生效。`dev-simplify` 默认不自行派生代理或调用其他 Skill；用户明确选择 `dev-delegate` 时，才将已启用约束、已确认建议、授权范围和验证条件交给既有流程，尚待确认的建议仍需等待确认。

调用 Skill 本身不扩大 Git、依赖或发布权限；这些操作按目标项目规则和当前任务已有授权处理。若组合使用两个 Skill，Codex CLI `0.162.0-alpha.17.2` 实测同一消息内的两个显式入口都会加载；Claude Code `2.1.296` 同一消息只直接加载第一个入口。Claude Code 上请在后续消息中再显式调用另一个 Skill；不要把同消息并列调用当作双入口均已加载的保证。

Codex / Claude 均注册此 Plugin。安装后新建对应客户端会话加载；仓库有文件或已经推送，不代表当前会话已注入新 Skill。该 Skill 执行时按目标项目授权与规则处理 Git，不自动取得全局修改或发布权限。

### 增强代码审查

`$personal-dev:dev-review` / `/personal-dev:dev-review` 仅在用户显式调用时运行。默认检查当前项目全部自有代码，包括已提交存量和工作区源码，即使没有 diff；指定目录、文件、模块、主题、commit 或 diff 时严格限定范围。它不依赖 Git，也不会启动原生 `/review`。

主模型在正式派发前一次性核对项目规则、范围、源码可读性、改动基线、报告位置与当前 Harness adapter。Codex 另核对可靠模型身份、当前派发工具名单与强度及解释器；Claude 核对原生 Agent 与非 fork 子代理能力。缺少必需项时集中输出 `BLOCKED`；生产权限、凭证、配额或实时运行数据属于可选证据，缺少时仍可进行代码层审查，并把相关量化结论列为待运行验证。审查和复核的实际型号/强度会在派发前展示；必要的独立复核只针对 P0/P1 或实质争议。

默认报告写到项目 `docs/personal-dev/reviews/<review-id>/report.md`，长审查的轻量进度记录与报告同目录。代码、配置和 Git 状态只读，审查过程不自动修复、提交或推送。报告区分 `COMPLETE`、`PARTIAL`、`BLOCKED` 执行状态与 P0–P3 风险等级；发现问题不会让执行状态自动变成 `BLOCKED`。没有高等级发现也不代表项目绝对安全。

### 远端运行诊断

`$personal-dev:dev-runtime-check` / `/personal-dev:dev-runtime-check` 仅在用户显式调用时运行。需要目标主机、SSH 连接方式、诊断对象和相关时间范围；信息足够时直接开始取证。默认只读并在聊天中汇报；只有用户明确要求保存时，才写入项目 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。明确要求修复后才执行授权范围内的必要操作，并遵守当前 Harness 的权限与审批。

Codex 使用其原生终端能力，Claude Code 使用原生 Bash 工具。诊断直接连接用户指定目标，先确认主机与进程、服务或容器身份；连接或命令失败时停止远端结论，不改查当前工作站。连接和每条远端命令都设置有限超时，仅对适用的暂时性错误有限重试。按症状有限采样，比较速率时记录两次计数、单位和真实间隔，并区分宿主机、容器与应用。排查请求量时区分浏览器到自有后端和后端到第三方；部署时间与故障相邻只表示相关性，不单独证明因果。不得记录凭据或启动长期采集。

## Agent 管理工具

### 本轮上下文估算（Codex）

`am-context` 只在用户显式调用 `$agent-manager:am-context` 后运行，不接受参数、模式或子命令。它按当前对话仍可见的内容分类并给出宽松、取整的区间；不调用工具、Python 或 tokenizer，不读取文件、会话、项目规则或配置。压缩前不可见的内容不计入，只估算当前摘要；隐藏指令只估算类别，不复述。分项区间上下界分别相加得到可见内容合计，不能当作真实总输入、窗口占用或剩余容量。Claude Code 不发现此入口。

### 编辑项目与冲突检查

`am-config` 仅支持 Codex 与 Claude Code。编辑前检查本次操作相关的项目/全局规则、Skills、Plugins、重复能力及实际加载边界；默认不展开无关能力。轻微重复、措辞差异或已有明确覆盖关系，用一两句话提醒；实质互斥、会改变其他行为的歧义或权限边界问题，详细给出双方原文、位置、触发条件、影响和最小方案，未明确取舍前停止整批写入。提示简短不构成覆盖、禁用或删除其他能力的授权。

同一入口支持只读检查，例如 `$agent-manager:am-config 只检查当前项目与全局规则的冲突，不修改`。仅要求查冲突时，全程只读并在报告后结束，不调用配置编辑器，也不创建探测环境、临时或报告文件。用户未限定范围时检查当前项目适用的指令、Skills、Plugins 与相关全局来源；指定范围时按范围检查。来源或加载状态不明标记 `UNKNOWN`，检查不完整标记 `PARTIAL`，不能声称完整无冲突。旧的独立冲突/更新入口已移除。

修改 Plugin 开关时，逐项指定完整 Plugin 身份及启用 / 禁用状态，例如：

```text
$agent-manager:am-config 在当前项目禁用 software-dev@agent-marketplace，启用 testing-automation@agent-marketplace
```

Claude 使用 `/agent-manager:am-config`。编辑分支只处理用户明确指定的项目操作：编辑 `AGENTS.md`、从准确来源安装 standalone Skill、准备注册项目 Plugin 与保存对应项目开关，或执行已安装 Plugin 的受支持开关。全局与项目外始终只读，不推荐组合、不提交或推送用户项目。更新安装副本仍使用下方[安装与更新](#安装与更新)步骤，维护仓库仍按[维护指南](maintenance.md#升级第三方-skill)同步。

#### 项目开关支持范围

以下版本与平台范围仅针对已安装 Plugin 的开关编辑器，不是项目文件准备或客户端能力的上限：

| 客户端与已验证版本 | 平台 | 项目 Plugin 开关 | 写入位置 |
| --- | --- | --- | --- |
| Codex `0.162.0-alpha.17.2`、`0.162.0-alpha.2` | Windows | 已安装的本地 Marketplace Plugin | `.codex/config.toml` |
| Claude Code `2.1.291`、`2.1.296` | Windows | 已安装的 Marketplace Plugin | `.claude/settings.json` |

Plugin 开关编辑器在其他操作系统返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`；这不限制 `AGENTS.md` 编辑、standalone Skill 或 Plugin 文件准备。Codex 与 Claude Code 的**单个 Skill 项目开关均不支持**。其他 Harness 输出 `BLOCKED / UNSUPPORTED AGENT`。未验证的 Codex / Claude 版本、目标缺失或歧义、配置损坏、有效项目层证据不足，以及 Codex 未受信任项目或 workspace-managed Plugin，均拒绝整批操作。Claude 的 `.claude/settings.local.json` 若对目标存在反向覆盖，也会整批拒绝。

standalone Skill 的项目安装与 Skill 开关不同：用户须指定准确来源和项目内目标，并通过当前 Harness 的加载目录、来源、重复、冲突及路径检查。已确认的发现目录为 Codex `.agents/skills/` 和 Claude Code `.claude/skills/`。复制所需资源并记录来源，不运行来源脚本或可能写用户 cache 的安装器。

项目 Plugin 分阶段处理：核对完整来源和项目路径，准备插件资源、项目 catalog / 当前客户端已核实的发现入口及对应开关，再验证实际发现、安装与加载。未安装不再直接阻止合法文件准备；新准备 Plugin 的文件和开关用文件工具编辑，不伪造 `installed=true` 或套用已安装开关编辑器。目录和开关保存不等于实际启用。

加载证据不足时，可在项目临时目录建立独立 `CODEX_HOME` / `CLAUDE_CONFIG_DIR`，限定配置、缓存、receipt 和日志的写入范围，不调用真实模型、不改变日常用户配置。当前 Codex CLI 的隔离实验表明，仅项目目录、catalog 和 `enabled=true` 不会自动加载该插件；因此分别报告“文件已准备 / 注册配置已保存 / 开关配置已保存 / 实际加载已确认或未验证”，catalog 条目写入不等于客户端已发现。原生安装需额外写用户记录时说明具体限制，不自动转成全局安装、关闭再项目启用的方案。旧 Skills 仅在替代入口实际加载已确认后按迁移授权移除。

`AGENTS.md` 默认编辑项目 Git/workspace 根文件；只有明确指定时才处理子目录。先核实当前 Harness 的真实指令链和遮蔽关系：Codex 同目录 `AGENTS.override.md` 优先；Claude Code v2.1.277+ 按祖先 `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`、版本与 Project instructions 设置选择是否加载。用户指定编辑文件时可以改文件本身，但不会自动添加引用或声称当前会话已加载。

未决实质冲突、身份歧义或写入边界不明时停止相关批次。实际加载未知不阻止已明确授权且来源、路径和格式已确认的项目内准备，但不能报告实际启用完成。全局与项目外始终只读；保存后新会话或重新加载才能确认会话状态。详细边界见 [项目文件预检](../plugins/agent-manager/skills/am-config/references/project-edits.md)、[Codex](../plugins/agent-manager/skills/am-config/references/codex-support.md) 与 [Claude](../plugins/agent-manager/skills/am-config/references/claude-support.md)。

## 安装与更新

Plugin 提供 Skill 内容，不代装 Playwright、Java、Vue 等运行依赖；使用时遵循目标项目的环境约束。

### Codex

从 Gitee 添加 Marketplace，再安装需要的分类；下面列出 Marketplace 中的六个 Plugin，可按需选择：

```powershell
codex plugin marketplace add git@gitee.com:vsattce/agent-marketplace.git --ref main
codex plugin add common-workflow@agent-marketplace --json
codex plugin add software-dev@agent-marketplace --json
codex plugin add engineering-tools@agent-marketplace --json
codex plugin add testing-automation@agent-marketplace --json
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
claude plugin install software-dev@agent-marketplace
claude plugin install engineering-tools@agent-marketplace
claude plugin install testing-automation@agent-marketplace
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

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 仓库已更新，客户端仍是旧内容 | 按对应客户端刷新安装副本，再新建会话 |
| 已安装，但当前聊天找不到入口 | 核对启用状态和当前会话清单，重新加载或新建聊天；磁盘存在不等于会话可用 |
| 不知道 Skill 是否自动执行 | handoff、三个管理入口和 personal-dev 仅手动；其他入口按任务匹配，启用不会自行执行 |
| 配置开关返回 BLOCKED | 查看具体原因及上方支持范围；安装成功不代表具备所有项目配置能力 |
| 想升级仓库里的第三方内容 | 在本仓库 Codex 聊天调用 `$upgrade`，见[维护指南](maintenance.md#升级第三方-skill)；它不刷新安装副本 |

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Skills](https://code.claude.com/docs/en/skills)、[Claude Marketplace](https://code.claude.com/docs/en/plugin-marketplaces)。
