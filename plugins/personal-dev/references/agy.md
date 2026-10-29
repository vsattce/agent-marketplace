# Antigravity CLI（agy） 审查适配

先读[子代理模型契约](subagent-models.md)：dev-review 只要求 reviewer，额外 worker 同样校验；不因此派发执行代理。主会话模型与用户配置不变，不运行 Codex Python helper。

原生工具为 `invoke_subagent`。从本轮实际工具取得可用模型、每个型号的 effort 与显式传参能力；reviewer 单参数无需 worker 型号或执行能力。名单、独立上下文、必要权限或覆写字段缺失，以及型号不可用或 effort 不支持时立即 BLOCKED，报告具体缺口。不 fallback、不继承默认、不换配置重试。

以当前 invoke_subagent schema 显式传 model 与实际 effort 覆写字段；不能套用 Codex 参数。使用干净上下文，按原生 task / 完成通知读取结果，不修改用户配置补能力。

派发前展示已提供角色的实际配置。全部审查与复核使用同一 reviewer；只传精简范围、项目规则、基线与证据，不复制完整聊天。审查代理只读、不修复、不提交、不派生代理。默认一个 reviewer，主模型核验证据后输出；严重或争议发现才定向独立复核。

等待、继续与中断使用当前原生接口并记录真实 ID。恢复前核对配置与状态，原生拒绝或配置不一致时停止。执行只读验证前读取[命令与资源契约](execution-resources.md)，跟踪后台 ID 至真实退出并释放自身资源。加载测试不证明真实模型审查已执行。

手动入口为 Codex `$personal-dev:dev-review`、Claude `/personal-dev:dev-review`、agy / dsh `/dev-review`；另外保留 `dev-simplify` 与 `dev-runtime-check`，以当前会话实际发现为准。
