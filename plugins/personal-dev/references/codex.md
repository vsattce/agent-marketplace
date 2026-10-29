# Codex 委派适配

仅用于已确认的 Codex Harness，先读[子代理模型契约](subagent-models.md)：dev-delegate / dev-auto 必填 worker + reviewer，dev-review 只要求 reviewer；额外 worker 同样校验。

## 模型校验与显示

根据本轮派发工具声明整理实际 ID、各型号 effort 及覆写字段，网页、缓存和默认配置不能替代。缺少 model / reasoning_effort 覆写或独立上下文时 BLOCKED。

三个入口共用 `skills/dev-delegate/scripts/select_models.py`；dev-auto 复用它，dev-review 的同名脚本调用它并传 `required_roles=("reviewer",)`。文本参数先用共享 `parse_arguments`，只传模型参数、不传入口名或任务正文；默认两角色必填，dev-review 传上述 required_roles。它整理值为 `<model>:<effort>`；缺项、重复或非法格式抛出含入口规范格式的 ValueError，必须停止。

将解析结果与本轮清单交给共享 `select_models`，或用以下 JSON stdin 协议运行对应入口脚本：

```json
{
  "worker": "6luna high",
  "reviewer": "6.1terra:HIGH",
  "inventory_source": "current-spawn-tool",
  "models": [
    {"id": "gpt-6-luna", "efforts": ["high"]},
    {"id": "gpt-6.1-terra", "efforts": ["high"]}
  ]
}
```

角色键用规范名或契约中的小写别名，值为 `<model>:<effort>` / `<model> <effort>`；models 每项仅含 id 与 efforts。不接受协议外字段、角色、默认值或主模型元数据。reviewer 单参数只需 reviewer、inventory_source、models，可只列其型号，无需 worker 或执行能力。

成功退出 0，返回 status=READY、已提供角色的 `{model,effort}` 与 display；reviewer 单参数只输出 reviewer 和一行 display。失败退出 2，返回 status=BLOCKED、安全原因及入口 usage，不回显不可信输入或异常。退出 0 且 READY 才按返回精确值展示并派发；helper 仅校验元数据，主模型仍核验来源和原生调用，READY 不代表已启动或已验证真实执行。

使用符合环境规则的现有 Python；缺失则 BLOCKED。不安装依赖或改变项目运行时、PATH、全局配置。

## 所有角色的原生参数

角色按模型契约确定，role 仅为 worker / reviewer 配置键，不猜造 agent_type。每次原生 `spawn_agent` 都显式传：

```text
model = result[role]["model"]
reasoning_effort = result[role]["effort"]
fork_turns = "none"
```

新代理用干净上下文，支持 fork_turns 时固定为 none；缺所需参数或原生拒绝、返回配置不一致即停止，按模型契约报告，不忽略配置或嵌套 Codex CLI。

## 派发与继续

执行命令、测试或清理前读取[命令与资源契约](execution-resources.md)。通过 `functions.exec` 包装 `exec_command` / `write_stdin` 时，至少返回 `{output, session_id, exit_code}`；只打印 `r.output` 会丢失未结束命令的 ID。有 `session_id` 时继续原会话直到取得退出码；`yield_time_ms` 和外层 `Script completed` 均不证明子进程退出。按当前实际工具字段执行，不编造接口。

V2 原编码代理返工优先用 `followup_task`，运行中补充信息用 `send_message`；V1 / 其他接口按实际声明用 resume / follow-up。等待、状态、中断用当前 wait / list / interrupt 工具，不编造参数或用 Codex 聊天管理工具创建用户可见新聊天替代子代理。

dev-delegate 默认单 worker 顺序执行；仅按共享编排安全条件并行，先启动本批再等待，使用实际槽位，不改配置补能力。dev-review 默认单 reviewer，主模型核证出报告，严重或争议发现再独立复核。

fresh coder、Final Reviewer、修复预算及 ledger 沿用入口契约。记录实际 Agent/task id、配置、阶段与轮次于可写 PLAN 或按需 ledger；恢复先核对当前配置与代理状态，保留计数和证据，通知延迟时不派发重叠写代理。CLI 包装与加载证据见[维护指南](https://github.com/vsattce/agent-marketplace/blob/main/docs/maintenance.md)，实际权限、额度及接口仍按本轮工具核对。
