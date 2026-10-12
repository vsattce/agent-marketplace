---
name: am-context
disable-model-invocation: true
description: 当前请求速览：只读查看当前 Codex thread 最新报告的模型请求用量与可确认的运行时上下文；仅在用户明确调用 $agent-manager:am-context 或 /agent-manager:am-context 后生效。
---

# 查看当前请求运行时上下文

只有用户明确调用 Codex 的 `$agent-manager:am-context` 或 Claude Code 的 `/agent-manager:am-context` 后才执行。普通聊天、引用命令、讨论名称或仅提到 `/context` 都不触发。只支持已确认的 Codex 与 Claude Code；其他 Harness 用中文提示“未知 / 当前 Harness 不受支持”。

## 模式

读取完整调用名之后的附加文本，只去除首尾空白，不从自然语言中提取模式：

- 无附加文本时使用内部模式 `summary`。
- 用户模式只接受精确的小写单值 `all`、`skills`、`tools`、`rules`、`help`。
- 显式 `summary`、`default`、大小写变化、多个值或其他文字均用中文提示“未知模式：<输入>”并显示用法，然后结束。
- `help` 以中文显示用法后结束。

用法：

```text
$agent-manager:am-context
$agent-manager:am-context all|skills|tools|rules|help
/agent-manager:am-context
/agent-manager:am-context all|skills|tools|rules|help
```

帮助、无效模式和不支持的 Harness 都不得执行检查脚本。

## 检查

确认本 Skill 的实际来源路径后，通过 `python -B` 调用该来源下的 `scripts/context.py` 一次，并传入解析后的内部模式、已确认的 Harness 名称和当前项目工作目录。脚本路径必须来自当前 Harness 已暴露的 Skill 来源；不要搜索用户目录、Plugin 缓存或其他安装位置来猜路径。若无法确认脚本路径或 Python 不可用，用中文报告“无法获取”并停止。保持当前项目工作目录，不要为调用脚本切换目录。

脚本只按当前 `CODEX_THREAD_ID` 查找一个会话日志；必须先确认日志元信息中的 thread ID 和 cwd 与当前会话、项目匹配，之后才读取该文件的用量事件。不得读取其他会话正文、私有数据库、项目文件、用户 Skills、Plugin、配置或缓存。不得把 `--active-skill`、调用名称、磁盘文件、缓存路径或工具调用名称当作 Skill 正文已进入请求的证据。

只把最新 `token_usage_record.payload.usage.input_tokens` 或 `event_msg.token_count.info.last_token_usage.input_tokens` 作为单次请求的实测输入量。忽略输出、累计 total、turn / thread usage，以及 `info=null` 的 rate-limit `token_count` 事件；同一响应镜像到多个日志事件时不可相加。模型窗口只在对应 `token_count` 事件明确报告，或对应 `token_usage_record` 的 `turn_id` 与唯一 `task_started` 事件匹配时展示；剩余量和百分比仅基于该请求输入量与对应窗口推导，并标为“推导近似”。新压缩记录会使此前用量失效，直至读到压缩之后的新测量。线程、cwd、记录或边界不能确认时显示“未知”，不得从其他会话补证。

当前 Codex 日志不暴露完整的最新请求输入快照，也没有可靠字段把历史消息、工具结果、规则、Skills、工具定义等逐项绑定到该请求。因此组成一律显示“未知”；不得把累计历史、压缩替换历史、截断的工具输出或静态来源估算冒充请求构成。Claude Code 当前没有可确认的请求用量记录时，同样显示“未知 / 无法获取”。

- 默认摘要用少量中文行报告：最新请求输入 token、同请求窗口、可得的推导近似占用 / 剩余，以及“组成无法获取”的原因。若窗口未知，不计算占用或剩余。
- `all` 展示组成类别及各自无法确认的原因。
- `skills`、`tools`、`rules` 只展示对应类别当前无法确认的状态，不扫描候选清单。

脚本内部状态转成中文展示：`MEASURED` 为“实测”，`UNKNOWN` 为“未知”，`UNAVAILABLE` 为“无法获取”，`AVAILABLE` 为“可获取”，`PARTIAL` 为“检查不完整”，`DERIVED / APPROX` 为“推导近似”。不直接向用户倾倒英文 JSON。

单独复现摘要检查时，将两个路径占位符替换为已确认的 Skill 来源绝对路径和当前项目工作目录；执行时保持当前项目工作目录不变：

```text
python -B "<已确认 Skill 来源目录>/scripts/context.py" --mode summary --harness codex --project "<当前项目工作目录>"
```

全程只读，不创建或修改文件、缓存和配置；不启动客户端、不启用 rollout tracing、不测试 MCP 连接，也不调用其他 Skill 或有副作用的工具。
