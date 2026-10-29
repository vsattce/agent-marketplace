---
name: sync-agy
description: 同步 agy 全局插件：用于用户要求将 agent-marketplace 当前工作区的产品插件安装或更新到 Antigravity CLI 全局；支持只读预检，排除仓库开发工具及其他客户端配置。
---

# 同步本仓库产品插件到 agy

仅在当前仓库使用。Codex 可调用 `$sync-agy`，Claude Code 可调用 `/sync-agy`，agy 可调用 `/sync-agy`。同步对象来自 `.agents/plugins/marketplace.json` 的产品 Plugin，不包括 `.agents/skills/`、项目 MCP、Superpowers 或本 Skill；不从 Claude / Codex 全局缓存批量导入。`testing-automation` 已并入 `engineering-tools`；若仍安装旧包，先报告并由用户通过原生 CLI 卸载，脚本在写入前停止以避免重复 `/playwright-cli`。

1. 从本文件目录解析 `../../..` 得到仓库根，确认 Git 根与 catalog，检查用户已有改动。同步当前工作区内容，不自动拉取、切换分支、升级来源、提交或推送。
2. 执行命令前读取[命令与资源契约](../../../docs/agents/execution-resources.md)：设置有限预算，保留未结束命令 ID，确认旧同步进程退出后才重试，不停止用户正在使用的 agy。先运行只读预检：

   ```powershell
   pwsh -NoProfile -File .agents/skills/sync-agy/scripts/sync.ps1 -CheckOnly
   ```

   脚本优先使用 PATH 中的 `agy`，Windows 可回退到 `%LOCALAPPDATA%/agy/bin/agy.exe`；也可用 `-AgyPath <实际程序路径>`。不修改 PATH、不安装或升级客户端。当前脚本要求 PowerShell 7，不运行项目 Python / Node。
3. 用户明确要求同步到 agy 全局时，已有请求即授权本次产品插件安装 / 更新，预检通过后运行同一脚本并去掉 `-CheckOnly`。用户仅要求检查时停在预检结果；仅自动匹配本 Skill 不构成全局写入授权。
4. 脚本逐项校验 manifest、调用原生本地安装、保留已有禁用状态，并检查安装清单、Skills 与配套资源。它仅处理 catalog 指定的插件名，保留其他来源的插件；失败立即停止，不卸载旧插件、不清空安装目录、不修改 trust / 权限 / 模型 / MCP 设置。
5. 报告 agy 版本、成功 / 未完成项与实际安装位置。提醒新会话或客户端重载后确认可用入口；安装校验不证明真实模型调用、SSH 或子代理业务流程已运行。重复运行用于刷新工作区副本，不等于持续自动同步。

该 Skill 只服务仓库维护，不注册进 Marketplace、不计入产品数量。
