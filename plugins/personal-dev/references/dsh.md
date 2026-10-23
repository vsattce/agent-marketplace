# DeepSeek Harness 桌面版适配

仅用于已确认的 dsh 桌面版，当前加载机制按 `0.2.1-rc.2` 核验。共享 SPEC / PLAN、角色职责、三轮修复与终审条件保持不变；以当前会话实际工具 schema 为执行依据。

## 入口与原生工具

用户直接输入 `/dev-prepare`、`/dev-delegate`、`/dev-auto`、`/dev-review`、`/dev-simplify` 或 `/dev-runtime-check`。dsh 的 `/name` 手动注入支持 `disable-model-invocation: true`；这些入口只处理用户明确调用，`dev-auto` 按共享组合契约读取执行正文。默认 Shell、文件和 SSH 操作使用当前会话原生工具及已有权限，不嵌套启动其他客户端或调用 Codex Python 选型器。

## 委派、验收与审查

1. 读取实际 `subagent` 工具描述，确认它使用 **spawn 干净上下文**、具备任务所需工具、可接收完成通知。默认 fork 会继承父会话，不满足共享流程的独立上下文要求；只有 fork 或缺少 spawn 时报告具体 `BLOCKED`，不自行修改桌面配置或由主模型代替全部编码 / 审查。
2. 编码与独立验收创建不同的 spawn 子代理，只传项目、SPEC / PLAN 路径、任务定位、必要规则和证据。审查代理明确只读、不派生代理、不提交。按共享编排判断有限并行，能力或范围不明时串行。
3. 默认继承原生子代理模型与思考配置，展示“dsh 原生默认 / 继承当前配置”；无法核实实际值时标 `UNKNOWN`。用户明确指定模型时，仅使用当前 schema 实际提供的参数及 `list_subagent_models` 暴露的已授权路由；缺少选型能力则报告限制，不改模型设置、不套用 Codex Luna / effort。
4. 子代理启动返回 ID，**不是任务完成**。保留该 ID，用原生完成通知 / 消息等待结果；只有已确认支持 continuation 时才用 `send_message` 续接。第三轮 fresh coder、独立复验和修复计数沿用共享角色契约，不因恢复或重建清零。
5. Final Reviewer 仍只按主 Skill 条件触发，使用不同的干净上下文。默认沿用原生验收配置，用户明确指定优先；不得宣称未实际执行的模型、SSH 或业务验收通过。

## 安装和加载边界

本仓库通过桌面版文件系统 Skill provider 加载完整产品目录；`agents/openai.yaml` 不控制 dsh。目录和隔离 provider 检查证明文件可被该版本读取；当前会话的 `/` 菜单、实际注入和子代理业务运行分别取证。工具缺失时保留已完成产物，不安装插件或修改用户级配置补能力。

依据：[Skills](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/packages/skill/tool-skill/README.md)、[原生子代理](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/packages/subagent/tool-subagent/README.md)。
