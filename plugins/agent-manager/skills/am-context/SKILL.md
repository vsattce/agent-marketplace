---
name: am-context
disable-model-invocation: true
description: 当前上下文自检：仅根据本轮模型已实际可见的内容，简要估算组成与可确认的请求用量；仅在用户明确调用 $agent-manager:am-context 或 /agent-manager:am-context 后生效。
---

# 当前上下文自检

只有用户明确调用 Codex 的 `$agent-manager:am-context` 或 Claude Code 的 `/agent-manager:am-context` 后才执行。只分析当前模型在本轮已经实际可见的内容；不得为自检调用工具、读取文件、会话、目录或配置，不调用其他 Skill。普通聊天、引用命令或只提到 Skill 名称都不触发。

## 模式

只解析完整调用名之后的附加文本，去掉首尾空白后按一个完整值匹配，不从自然语言中提取。无附加文本使用 `summary`；只接受精确小写单值 `all`、`skills`、`tools`、`rules`、`help`。显式 `summary`、大小写变化、多个值或其他内容均显示 `未知模式：<输入>` 和中文用法。保留两种客户端的调用拼写：

```text
$agent-manager:am-context
$agent-manager:am-context all|skills|tools|rules|help
/agent-manager:am-context
/agent-manager:am-context all|skills|tools|rules|help
```

`help` 和未知参数只说明用法，不检查上下文。

## 分析与估算

按本轮仍可见的材料归类，不输出内部推理，也不复述受保护的 System / Developer 正文、凭据或私有会话正文。类别可合并简述：对话与本轮消息、压缩摘要、System / Harness / Developer 指令类别、项目规则、Skill 发现元数据、实际可见的已加载 Skill 正文、当前暴露的工具 / MCP / Plugin 信息、工具结果及其他运行时信息。只引用本轮上下文里仍可见的内容和工具结果。

只有确由 Harness 直接提供且明确属于本轮请求的 input 或 window 数值才标“实测”。上下文中的示例、旧日志、历史轮次、默认窗口、配置值、累计值和用户手写引用都不是本轮实测。没有直接数值就标“未知”，不查找或补证。

LLM 只能粗略估计当前可见组成，写“估算：约 X 千”或“估算：约 X–Y 千”这类量级，不用 tokenizer、逐 token 计数或精确假数。组成估算不等于真实总输入；未知类别不填零，也不从已知部分反推精确总量或差额。若压缩前原文已不可见，只计可见摘要一次。分类时一段内容只归入一个类别；估算占用时，当前可见的真实重复文本仍计入，不因名称或展示列表去重而抹去。名称、模式、命令和路径保持原样；状态及说明使用中文。

只有 input 与 window 都有本轮可靠的实测值时，才可推算占用和剩余，并标“推导近似”。若 input 大于 window 或两者冲突，保留实测值，将推导标“未知”并说明冲突，不自行修正或猜测。

summary 保持简短，按可用信息填写以下骨架；不适用项可省略：

```text
本轮请求：input 实测/未知；window 实测/未知（注明来源）
可见组成：估算/未知（简述类别与来源）
占用与剩余：推导近似/未知（仅在可推导时填写）
```

`all` 按上述类别展开可见内容、估算状态和可确认来源。

## 分类模式

- `skills`：只总结本轮实际可见的 Skill 发现元数据（`name`、`description`、已注入路径）与仍可见的已加载正文。只有正文实际出现在当前可见上下文中才算已加载；磁盘、清单、缓存、调用名或历史摘要中的提及都不能证明正文已加载。同名 Skill 只列一次；真实重复出现的文本仍按其可见占用估算。
- `rules`：只概述当前可见的项目规则，以及 System / Harness / Developer 指令的类别和大意；不披露受保护正文。
- `tools`：只总结本轮实际暴露的工具、MCP 和 Plugin 信息。区分可见的名称 / 描述与完整定义；延迟工具的登记或可懒加载说明不代表其 schema 已可见。不得据名称、namespace 或缓存路径推断 Plugin 已安装或启用。

以上模式均不读取或探测其外部来源。任何当前不可见的类别标“未知”，不得用历史快照或其他会话补全。
