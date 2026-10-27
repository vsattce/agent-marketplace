# DeepSeek Harness 桌面版适配

仅用于已确认的 dsh 桌面版，当前加载机制按 `0.2.1-rc.2` 核验。共享 SPEC / PLAN、角色职责、三轮修复与终审条件保持不变；以当前会话实际工具 schema 为执行依据。

## 入口与原生工具

用户直接输入 `/dev-prepare`、`/dev-delegate`、`/dev-auto`、`/dev-review`、`/dev-simplify` 或 `/dev-runtime-check`。dsh 的 `/name` 手动注入支持 `disable-model-invocation: true`；这些入口只处理用户明确调用，`dev-auto` 按共享组合契约读取执行正文。默认 Shell、文件和 SSH 操作使用当前会话原生工具及已有权限，不嵌套启动其他客户端或调用 Codex Python 选型器。

入口首先遵守[子代理模型契约](subagent-models.md)：dev-delegate / dev-auto 校验本次显式 worker + reviewer，dev-review 只要求 reviewer，额外提供 worker 时同样校验；主会话模型不变。

## 委派、验收与审查

1. 读取实际 `subagent` 工具描述，确认它使用 **spawn 干净上下文**、具备任务所需工具、可接收完成通知。默认 fork 会继承父会话，不满足共享流程的独立上下文要求；只有 fork 或缺少 spawn 时报告具体 `BLOCKED`，不自行修改桌面配置或由主模型代替全部编码 / 审查。
2. 编码与独立验收创建不同的 spawn 子代理，只传项目、SPEC / PLAN 路径、任务定位、必要规则和证据。审查代理明确只读、不派生代理、不提交。默认单 worker 顺序执行，仅多个独立任务确有收益或用户要求且共享安全条件满足时启用并行；ledger 按调度或恢复需要启用。dev-review 默认单 reviewer，主模型核证出报告，严重或争议问题再独立复核。
3. 用当前 schema 实际提供的字段及 list_subagent_models 暴露的已授权路由核验入口必需及额外提供的配置；reviewer 单参数无需 worker 型号或执行能力。执行型代理使用 worker；审查、SPEC / PLAN 检查、验证结果、回归风险和独立验收使用 reviewer。每次 subagent 显式传对应模型路由与原生 effort 覆写字段；缺少字段、名单或支持证据，模型不可用或 effort 不支持时立即 BLOCKED 并说明。不继承原生默认、不以 UNKNOWN 继续、不套用 Codex 参数、不改模型设置。只展示已提供角色；多个 Worker 共用 worker，多个 Reviewer 共用 reviewer。原生拒绝或实际配置不一致时停止，不换配置。
4. 子代理启动返回 ID，**不是任务完成**。保留该 ID，用原生完成通知 / 消息等待结果；只有已确认支持 continuation 时才用 `send_message` 续接。通常修一次并复验，持续存在 blocker 才继续，最多三轮。fresh coder 仅原代理不可恢复、上下文失效或同根因反复无进展时启用，独立复验和计数沿用共享契约，不因恢复或重建清零。
5. Final Reviewer 仍只按主 Skill 条件触发，使用不同的干净上下文和同一 reviewer，不自动升降强度；按需 fresh coder 使用同一 worker。恢复原代理前核对配置一致，无法核验或不一致则停止续接并说明。主模型始终整体检查与最终 fresh verification；不得宣称未实际执行的模型、SSH 或业务验收通过。

## 安装和加载边界

本仓库通过桌面版文件系统 Skill provider 加载完整产品目录；`agents/openai.yaml` 不控制 dsh。目录和隔离 provider 检查证明文件可被该版本读取；当前会话的 `/` 菜单、实际注入和子代理业务运行分别取证。工具缺失时保留已完成产物，不安装插件或修改用户级配置补能力。

依据：[Skills](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/packages/skill/tool-skill/README.md)、[原生子代理](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/packages/subagent/tool-subagent/README.md)。
