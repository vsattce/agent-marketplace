# agent-marketplace 全项目自有代码审查报告

归档说明（2026-10-12）：从原 docs/reviews 目录迁入，保留历史结论，更新已迁移文件的链接；继续作为本地未提交记录。

COMPLETE

本轮没有确认 P0/P1。保留三项 P2：一项经纯内存复现的来源漏项问题，以及两项仅在 POSIX 和特定文件/并发条件下成立的配置器风险。当前 Windows 隔离测试没有触发这三项问题；当前实际来源配置也没有重复键。

## 范围与基线

- 用户请求：完整检查当前项目，使用 GPT-6 Luna 子代理，生成报告文档。
- 项目根：`E:\WorkSpace\agent-marketplace`。
- 开始时间：2026-10-11 11:22:36，时区 Asia/Shanghai。
- 收尾基线核验：2026-10-11 11:34:59，时区 Asia/Shanghai。
- Git 基线：`main`，`b661a673831eb04dc47e8574e8968263b5c5e353`，起始与 `origin/main` 同步；暂存、未暂存和未跟踪文件均无改动。
- 范围：全部现有自有代码与流程，包括 agent-manager、personal-dev、同步脚本、产品 catalogs/manifests、项目自有维护入口及直接相关测试和当前使用文档。
- 排除：第三方 Skill 正文、Superpowers 与 plugin-dev 上游参考快照的内部实现、生成物、依赖、二进制和历史报告。需要核实自有包装/引用时只检查直接资源和来源 metadata。
- 适用规则：根 AGENTS.md、用户提供的工程标准，以及明确调用的 dev-review/dev-delegate。当前产品支持 Codex 与 Claude Code。
- 执行方式：代码层审查，加仓库现有 opt-in 隔离客户端加载测试。仅生成本报告与进度记录；审查代理只读。

## 参与模型与方式

| 角色 | 实际配置 | 职责 |
| --- | --- | --- |
| 主代理 | 本轮可信上下文声明 GPT-6 家族，未提供精确变体 ID | 预检、原生派发、运行证据、候选裁决、最终报告 |
| `/root/review_config` | `gpt-6-luna` / `xhigh`，干净上下文 | agent-manager、项目配置事务/安全和来源比较 |
| `/root/review_sync_workflow` | `gpt-6-luna` / `xhigh`，干净上下文 | sync、personal-dev、双端包装及自有维护流程 |
| `/root/verify_candidates` | `gpt-6-luna` / `max`，干净上下文 | 定向复核三个候选，核准触发路径与分级；没有重扫全项目 |

当前会话是 Codex Harness，使用原生 `collaboration.spawn_agent`。用户明确指定“sub 6luna”，模型 helper 通过显式 `model_override=gpt-6-luna` 核验当前工具允许的型号和强度，结果 `READY`；没有推测主模型精确变体，也没有降级。未嵌套客户端执行真实模型审查。

本次目标是检查与报告，未提出代码修复任务，因此 dev-delegate 的编码/两轮返工流程不适用；已读取其 adapter 与角色契约，复用干净上下文和独立核验原则。

## 覆盖情况

| 模块或维度 | 状态 | 实际覆盖与结论 |
| --- | --- | --- |
| agent-manager / am-config | 已覆盖，有条件风险 | 完整配置编辑器、Skill、四个引用文件及直接测试；两端能力校验、字节保留、拒绝非法批次、锁、原子替换、并发和回滚。保留 POSIX 两项条件风险 |
| agent-manager / am-update | 已覆盖，有发现 | 来源与 lock 身份匹配、固定 SHA、目录存在、网络失败分类、请求去重、20 秒超时与 10 MB 响应上限；保留重复键导致漏项的问题 |
| agent-manager / am-conflict | 已覆盖，无发现 | 只读调查、来源/安装/启用/会话可见的区分、项目与相关全局路径边界、UNKNOWN/PARTIAL 流程 |
| scripts/sync.py 与来源记录 | 已覆盖，有发现 | 来源校验、四个第三方分类的写入白名单、快照/许可证、暂存发布、lock 合并、失败恢复及现有测试；与 am-update 合并同一重复键根因 |
| personal-dev | 已覆盖，无发现 | 两个 Skill、共享模型选择与审查 adapter、两端 Harness 引用、角色交接、独立复核、有限返工、agents metadata 与相关测试 |
| 双端 catalogs / 产品 manifests | 已覆盖，无发现 | 六个 Plugin 的两端入口、名称、目录与资源。当前 13 个第三方来源、13 条 lock 记录一致，另有 5 个自有 Skills，共 18 个产品 Skills |
| 项目自有维护入口 | 已覆盖，无发现 | 两端 upgrade、claude-plugin-dev 包装、根规则入口、.codex/config.toml 与测试。上游开发工具没有进入产品注册 |
| 当前 README / 使用 / 维护文档 | 已覆盖，无发现 | 支持范围、手动调用、安装入口、运行环境、测试隔离与历史证据边界；未用旧版本记录代替本轮事实 |
| 现有自有测试代码 | 已覆盖 | 12 个 Python 测试文件，覆盖同步、配置、包装、模型选择、双端 loader 与项目工具入口；源码审查与运行证据分别记录 |
| Windows 客户端加载与配置行为 | 已运行验证，无失败遗留 | 使用现有隔离 fixture；133 个用例均已有通过证据，具体首轮与定向复验结果见下文 |
| 性能、内存、第三方请求 | 已覆盖代码路径，无额外发现 | 自有脚本按调用结束，无常驻调度/无限重试；检查请求超时、响应限制和去重。不推断未知配额或给出性能数字 |
| 磁盘与长期运行 | 已覆盖适用路径，无额外发现 | 检查暂存/发布/恢复和客户端 fixture 清理；POSIX 临时文件遗留风险纳入下文。无自有长期运行服务 |
| 常驻服务、数据库事务、浏览器页面 | 不适用 | 自有产品为 Skill 流程与 CLI 辅助脚本，没有上述业务实现 |
| POSIX 客户端与竞争/FIFO 实测 | 未运行，限制已记录 | 本轮环境为 Windows，不能把静态条件风险写成已实测漏洞 |
| 第三方正文、法律与生产/真实模型流程 | 排除或未运行 | 第三方内部实现和许可证法律充分性不在自有代码范围；未连生产或执行全部 Skill 业务流程 |

两个审查代理分别完成独立范围。主代理完整核对了 loader 测试机制、候选直接代码、运行输出与源码基线；同根因来源问题经同步审查代理一轮定向补证。所有候选只做一次定向补证，没有自动修复或扩大开发范围。

## 发现

### P0 / P1

没有已确认的 P0/P1。初审将 POSIX 目录竞争列为 P1/P2 候选，独立复核与主代理均裁决为 P2 条件风险，理由见第二项。

### 1. P2：重复来源映射键会漏掉前一组 Skills

- **证据状态：已确认（纯内存 fixture 复现）；实际触发依赖配置误写。**
- **位置：** [check_sources.py](E:/WorkSpace/agent-marketplace/plugins/agent-manager/skills/am-update/scripts/check_sources.py:40) 第 40–47 行；[sync.py](E:/WorkSpace/agent-marketplace/scripts/sync.py:50) 第 50–58 行。同步对旧记录的保留提示在第 254–257 行。
- **触发：** `sources.yaml` 在 `groups` 下重复定义同一个分组键，例如两段 `common-workflow` 分别列出 alpha 和 beta。每一段本身都可以满足现有结构校验。
- **影响：** 默认 YAML 解析先把重复键折叠，后续校验和遍历只看到 beta。am-update 能正常返回 beta 的 LATEST，却没有检查 alpha。同步也只接受后一个组，前组来源不会更新。若旧 lock 已含被省略项，同步会打印 unlisted 保留提示，旧快照和 lock 不会自动删除；这是漏检查/漏同步与长期过期风险。
- **直接证据：** 主代理将文件读取与上游 query 都替换为内存 fixture，无文件写入、无网络请求。两段声明 alpha/beta，lock 含两项合法记录，实际输出：

```json
{"declared_names":["alpha","beta"],"am_update_rows":[{"Name":"beta","Status":"LATEST"}],"sync_accepted_names":["beta"],"writes":0,"network_requests":0}
```

- **当前状态：** 当前真实配置的四个分组键唯一，13 个来源与 lock 对齐，尚未触发。不要把此发现解释为当前 Marketplace 已少装 Skill。
- **建议：** 在开始上游查询、fetch 或写入前，拒绝重复 YAML mapping key；两条读取流程使用一致校验。补一条重复组键回归用例，验证报错且没有网络调用或快照/lock 改动。JSON lock 的重复键也可沿同一输入完整性策略处理，本轮最直接的复现是 YAML 分组键。
- **复核：** 同步审查代理与独立 Luna max 均支持保留 P2；主代理合并 am-update/sync 的同一根因。

### 2. P2：POSIX 目录竞争可能把配置写入导向项目外

- **证据状态：条件风险；静态可达路径已复核，未在 POSIX 运行复现。**
- **位置：** [configure_project.py](E:/WorkSpace/agent-marketplace/plugins/agent-manager/skills/am-config/scripts/configure_project.py:355) 第 355–382 行、408–425 行及 458–464 行。
- **触发：** 在 POSIX 上运行已认可版本的配置器，且同一时段另一本地主体能重命名/替换项目 `.codex` 或 `.claude` 目录。在第 408/409 行安全检查之后、第 410 行创建锁或第 414 行创建 staging 之前，将该目录换成指向项目外可写目录的 symlink。
- **影响和证据：** Windows 会持有拒绝 rename/delete 的目录句柄；POSIX 分支直接 yield。随后 lock 和临时配置仍按可变路径创建，可能落到项目外。第 422 行重新检查通常会拒绝最终发布，但 finally 中的第 459/463 行也会拒绝当前链接路径，外部临时文件/锁可能遗留，违反仅项目写入的边界。
- **最终发布的精确交错：** 在原配置不存在、original=None 的例子中，并发者可让第 410/414 行在外部目录创建 lock/staging，再临时恢复真实项目目录，使第 422 行路径检查和第 423 行原值比较通过，随后在第 425 行前重新链接到含 staging 的外部目录。源与目标此时同时解析到该外部目录，最终配置也可在项目外创建。写后第 428 行仅核对内容，不重新核验路径。此序列属于静态可达分析，没有在 POSIX 实验复现。
- **结论边界：** 单纯在最终 replace 前换父目录时，源文件可能变得不可达而直接失败；需要上述精确多次交错才能把最终发布导向外部。已有全局配置另需满足第 411 行读取值与 original 相同等条件，不能笼统断言必然覆盖用户全局配置。未证实当前 Windows 有同一漏洞，也没有权限提升证据。
- **建议：** 若维护范围保持为已验证 Windows 环境，入口明确拒绝未验证的 POSIX 写入；若要继续支持 POSIX，则使用绑定目录句柄的相对文件操作及禁止跟随链接的打开方式，并补受控目录交换验证。
- **独立裁决：** Luna max 确认早期锁/staging 写入与精确交错下的外部配置发布均有条件可达，驳回 P1 级别及普遍覆盖全局配置的表述；主代理核对完整序列后保留 P2 条件风险。

### 3. P2：POSIX FIFO 配置路径可能使一次调用无限等待

- **证据状态：条件风险；静态读取路径已复核，未在 POSIX 运行复现。**
- **位置：** [configure_project.py](E:/WorkSpace/agent-marketplace/plugins/agent-manager/skills/am-config/scripts/configure_project.py:82) 第 82–92 行、310 行、490 行。
- **触发：** 有效版本/inventory 通过预检后，项目 `.codex/config.toml`、`.claude/settings.json` 或 `.claude/settings.local.json` 恰为 FIFO，且没有写入端提供内容。
- **影响和证据：** 路径检查拒绝 symlink/reparse 和多硬链接的普通文件，却不要求现有配置是普通文件。FIFO 可通过这些检查；后续直接 read_bytes/read_text 没有读取超时，会阻塞单次配置调用。普通目录会快速读失败，不属于此挂起情形。
- **当前边界：** 触发需要特殊项目文件或本地并发替换，属于局部、有限条件风险；当前 Windows 测试没有触发证据。
- **建议：** 配置与 local 覆盖文件在读取前要求普通文件；对并发边界用打开后的文件描述符核验文件类型与身份。特殊文件应立即返回结构化 BLOCKED。
- **独立裁决：** Luna max 支持 P2 条件风险，未提升为核心功能无条件不可用。

### 未纳入缺陷的观察

- `explicit_invocation` 是调用者提供的声明，脚本依赖 Skill 的授权与发现证据契约；本仓库没有将该字段当成独立身份凭证的实现要求，不作为已确认授权漏洞。
- 原子替换对 Windows 自定义 ACL 的具体影响未核实，且没有当前受影响配置证据，未把它列为缺陷。
- 首轮两个 CLI 测试的 UTF-8/GBK 不一致由本次测试进程设置引入，经定向复验解决；没有据此改动产品或虚增代码缺陷。

P3 没有单列问题。纯风格、缺少最佳实践或缺少测试本身未计入缺陷。

## 验证证据

- 项目要求 Python >=3.12；`mise current` 与 `python --version` 均核实为 3.12.13。复用 uv 已有环境与缓存中的 PyYAML 6.0.3、tomlkit 0.13.3，未安装/升级依赖或修改运行时。
- 本轮实测客户端：`codex-cli 0.162.0-alpha.17.2`、`2.1.296 (Claude Code)`。
- 全量 unittest 同时开启 `AGENT_MANAGER_CODEX_TESTS=1` 和 `AGENT_MANAGER_CLAUDE_TESTS=1`：133 项，47.034 秒，131 通过、2 CLI 编码错误、0 跳过。
- 首轮为工具输出设置 `PYTHONIOENCODING=utf-8`，子进程输出中文 UTF-8，但两项测试使用 `subprocess(text=True)` 的父进程默认 GBK 解码，出现 UnicodeDecodeError。随后仅对测试进程设置 `PYTHONUTF8=1` 对齐父子编码，定向复验原两失败项：2 项全部通过，0.081 秒。未改代码；没有声称单次全量运行 133 项全部通过。
- 已通过的真实客户端证据覆盖：Plugin 安装/发现、手动入口、personal-dev 显式注入与普通提示不注入、Claude 原生 Agent schema、项目 upgrade/规则入口、两端项目 Plugin 覆盖与限制、Codex untrusted 项目层不生效。
- 本轮 Claude 2.1.296 的 Agent schema 包含 `effort`；维护文档中 2.1.291 不含该字段的记录是历史版本证据。
- 隔离 fixture 使用临时客户端配置与 localhost 捕获器；不调用真实模型、不执行 Skill 正文，不改日常全局客户端配置。
- 测试生成的 `claude/fswatch-probe-*` 临时目录已按显式文件路径及空目录清理。原有忽略目录 `.skill-sync-plugin-dev-task` 保留。
- 收尾 `git diff --check`、暂存区检查通过；HEAD 仍为原基线，tracked 与 staged 差异为空，只有本目录报告与进度记录新增。

实际运行入口为已有 uv 环境的 `python.exe -B -m unittest discover -s tests -v`；测试进程设置规范项目 TMP/TEMP、双端 opt-in，并通过进程级 PYTHONPATH 复用已缓存 tomlkit。定向复验入口为 `python.exe -B -m unittest test_personal_dev.SelectModelsCliTests.test_ready_cli_prints_json_and_exits_zero test_personal_dev_review.ReviewModelAdapterCliTests.test_ready_cli_prints_contract_and_exits_zero -v`，工作目录 `tests`。

## 待验证与限制

- 客户端 loader 请求捕获证明发现、注入与配置行为，不证明每个 Skill 的完整业务流程或模型推理质量。
- 未连接生产、未发真实上游 GitHub 更新请求、未同步第三方快照、未压测外部服务。
- 上游配额、实际长时运行、宿主机物理磁盘写入及模型成本没有实测，不给量化结论。
- 第三方 Skill 与上游工具快照正文不属于本次自有代码审查范围；注册、引用与来源边界属于范围。
- 全局覆盖、自定义 ACL、POSIX FIFO 与目录竞争的运行结论没有实测，不把静态风险冒充当前 Windows 故障。

## 交付与执行状态

执行状态为 COMPLETE：约定的全部现有自有代码及直接相关入口、配置、测试已完成检查，三个候选已核对证据与独立裁决，报告明确列出实际覆盖、排除与未运行验证。发现 P2 不改变执行完成状态；结论只适用于上述代码基线与证据。

源码、配置和 Git 基线未改变，没有修复、提交或推送。仅交付本报告与同目录轻量进度记录，符合本次 dev-review 的只读交付边界。

## 修复回访（2026-10-11）

本报告以上内容保留原审查基线。用户随后授权修复，三项问题已按最小方案处理，并通过独立 Luna max 验收、主代理终审及147项双端隔离测试。修复已随 `d9b95c9` 推送至 main；Plugin 开关编辑器现在明确仅支持 Windows。

完整结果及验证边界见 [修复与复验报告](E:/WorkSpace/agent-marketplace/docs/personal-dev/tasks/2026-10-11-review-fixes/acceptance.md)。
