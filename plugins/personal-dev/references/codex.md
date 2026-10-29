# Codex 审查适配

仅用于已确认的 Codex Harness。先读[子代理模型契约](subagent-models.md)：dev-review 只要求 reviewer，额外 worker 同样校验。

## 模型校验与显示

从本轮派发工具取得实际 ID、effort 支持与覆写字段；网页、缓存和默认配置不能替代。缺少 model / reasoning_effort 覆写或独立上下文时 BLOCKED。

本 Skill 的 `skills/dev-review/scripts/select_models.py` 调用同目录 `model_validation.py`，以 `required_roles=("reviewer",)` 校验。文本参数先调用该实现的 `parse_arguments(arguments, required_roles=("reviewer",))`，只传提取的模型参数，不传任务正文。缺项、重复或非法格式抛出 ValueError，必须停止。

JSON stdin 示例：

```json
{
  "reviewer": "6.1terra:HIGH",
  "inventory_source": "current-spawn-tool",
  "models": [{"id": "gpt-6.1-terra", "efforts": ["high"]}]
}
```

协议保留已显式提供的可选 worker 校验；没有 worker 时不要求其型号或执行能力。models 每项只包含 id 与 efforts，不接受协议外字段、旧角色或主模型元数据。成功退出 0，返回 status=READY、已提供角色的 `{model,effort}` 与 display；失败退出 2，返回 BLOCKED、reasons 与 usage，不回显原始输入。

## 原生审查

每次原生 `spawn_agent` 显式传 `model = result[role]["model"]`、`reasoning_effort = result[role]["effort"]`、`fork_turns = "none"`，其中 role 为 reviewer。用干净上下文，只传范围、项目规则、基线和必要证据；禁止写入、修复、提交与派生代理。

默认一个 reviewer，主模型核证出报告，严重或争议发现才定向独立复核。记录真实 Agent/task ID；补充信息、等待、继续或中断按本轮工具 schema，不用用户聊天管理工具替代子代理，不编造工具字段。恢复前核对配置与状态，缺能力或原生拒绝时停止。

执行只读验证与清理前读取[命令与资源契约](execution-resources.md)。通过 `functions.exec` 包装命令时保留 output、session_id、exit_code，继续原会话直到取得退出码；工具 yield 或包装层结束不证明进程已退出。
