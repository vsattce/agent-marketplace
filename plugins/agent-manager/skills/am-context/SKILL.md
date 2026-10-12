---
name: am-context
disable-model-invocation: true
description: 上下文速览：只读检查当前会话的组成、来源和加载证据；仅在用户明确调用 $agent-manager:am-context 或 /agent-manager:am-context 后生效。
---

# 检查当前上下文组成与来源

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

确认本 Skill 的实际来源路径后，通过 `python -B` 调用该来源下的 `scripts/context.py` 一次，并传入解析后的内部模式、已确认的 Harness 名称、当前项目工作目录和 `--active-skill am-context`。脚本路径必须来自当前 Harness 已暴露的 Skill 来源；不要搜索用户目录、Plugin 缓存或其他安装位置来猜路径。若无法确认脚本路径或 Python 不可用，用中文报告“无法获取”并停止。保持当前项目工作目录，不要为调用脚本切换目录。所有面向用户的摘要、`all` / `skills` / `tools` / `rules` 详情与帮助均用中文轻量整理，只翻译已有字段的标签、状态及说明；原样保留命令、路径、Harness、Plugin / Skill / MCP 名称和必要的内部技术标识，不向用户直接倾倒英文 JSON。摘要默认用少量行展示脚本已提供的字段：最新报告请求的输入 / 窗口 token 与已标注的推导近似剩余量 / 百分比，规则、Skill 元数据、Skill 正文、Plugin 元数据、已知项目配置这五类 `known_breakdown` 的状态、文件数、字节 / token 估算与完整度，统一估算方法，加载状态，以及规则 / Skills / Plugins / Tools 的来源数量。`summary` 和 `all` 的 `known_breakdown` 已由脚本汇总，直接展示已有数值，不重算。内部状态按以下方式展示：`MEASURED` 为“实测”，`ESTIMATED` 为“估算”，`UNKNOWN` 为“未知”，`DERIVED / APPROX` 为“推导近似”，`UNAVAILABLE` 为“无法获取”，`PARTIAL` 为“检查不完整”，`COMPLETE` 为“采集完成”，`FACT` 为“已确认”，`NOT_RUN` 为“未采集”，`AVAILABLE` 为“可获取”。估算方法分别显示为“o200k_base 分词估算”或“UTF-8 字节数代理”，不称为精确 token 数；加载状态未知时明确显示“加载情况：未知”。用量缺失时显示 token 状态“未知”及单独的数据可用性。不得为展示结果再次扫描 / 读取统计文件，也不得自行估算或重新计算数值；不得根据目录、缓存、名称或静态配置把未知的会话加载状态提升为事实。

帮助和无效模式无需调用脚本，使用中文说明，例如：

```text
用途：只读查看当前 Codex 或 Claude Code 上下文的来源、状态与加载证据。
用法：$agent-manager:am-context [all|skills|tools|rules|help]
用法：/agent-manager:am-context [all|skills|tools|rules|help]
不附加模式时显示简短摘要；help 显示此说明。
```

脚本要求 Python 3.11 或更高版本，使用内置标准库，不安装依赖。它只读检查项目与已确认 Harness 的配置来源，并进行有界读取；估算仅在 `tiktoken` 已安装且其编码数据已有本地缓存时使用该 tokenizer，否则以 UTF-8 字节数作为明确标注的大小代理，不联网、不创建或填充缓存。它只输出路径、名称、状态和估算，不输出配置值、规则正文、工具定义或系统 / 开发者指令。文件存在或配置登记不代表当前会话已加载；缺少加载证据时展示“未知”，检查不完整时展示“检查不完整”。

以下是单独复现摘要检查的命令模板。将两个路径占位符替换为已确认的 Skill 来源绝对路径和当前项目工作目录；执行时保持当前项目工作目录不变：

```text
python -B "<已确认 Skill 来源目录>/scripts/context.py" --mode summary --harness codex --project "<当前项目工作目录>" --active-skill am-context
```

Context token usage 只在 Codex 的 `CODEX_HOME/sessions` 中按精确 `CODEX_THREAD_ID` 找到唯一会话文件、并验证文件元信息中的 thread ID 与 cwd 均匹配当前项目后才读取用量事件。逐条解析时只提取 session 元信息、`token_count` 的 `last_token_usage.input_tokens` 与模型上下文窗口、顶层 `type=compacted` 标记，以及兼容的 `event_msg` 压缩事件；压缩标记用于作废较早的用量。每条记录处理后立即丢弃完整解析对象。其他字段和对话正文不得输出、写入文件、保留或传给模型；不得读取其他会话或私有数据库。最新用量缺失 / 无效、线程或 cwd 不匹配、文件不唯一，或压缩后没有更新的有效用量时，token 状态展示为“未知”，并单独展示数据可用性“无法获取”或“部分可用”；Claude Code 未公开当前用量时展示“未知 / 无法获取”。剩余量和百分比是基于最新报告请求及上下文窗口推导的近似值。字节估算必须标为近似值，不得称为精确 token 数。

全程不创建或修改文件、缓存和配置；不启动客户端、不刷新安装状态、不测试 MCP 连接，也不调用其他 Skill 或有副作用的工具。
