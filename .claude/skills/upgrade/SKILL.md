---
name: upgrade
description: 升级第三方 Skills：用于升级或同步 agent-marketplace 仓库中 sources.yaml 配置的第三方 Skills，复用现有同步脚本并完成验证、提交和推送；只读版本检查、其他项目依赖升级和 Codex 安装缓存刷新另行处理。
---

# 升级本项目第三方 Skills

这是 Claude Code 的项目入口，调用 `/upgrade`。执行正文只有一份：先读取本入口目录相对路径 `../../../.agents/skills/upgrade/SKILL.md`，然后按该文件完整执行环境核对、同步、验证与 Git 收尾。

仓库根从共享正文所在目录解析，不从安装缓存或其他项目猜测；用 Git root 与 sources 文件确认。共享正文缺失或当前目录不属于本仓库时停止，不自行创建同步逻辑、不执行其他仓库的升级。
