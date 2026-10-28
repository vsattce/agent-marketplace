---
name: sync-dsh
description: 同步 dsh 桌面版 Skills：用于用户要求检查或同步本仓库产品插件内容到已安装的 DeepSeek Harness 桌面版；保留资源与手动调用边界，排除仓库开发工具。
---

# 同步产品内容到 DeepSeek Harness 桌面版

仅用于当前 agent-marketplace 仓库。Codex 使用 `$sync-dsh`；Claude Code / agy 使用 `/sync-dsh` 项目入口。读取 `.agents/plugins/marketplace.json` 中的产品，只同步五个产品包的共享 Skills 与资源；`am-context` 仅 Codex，仓库开发 Skills、Superpowers、MCP 和本入口不导出。

1. 检查 Git 状态，保留用户改动；确认用户指定的是已安装的 **桌面版**及其 `DeepSeek Harness.exe`，读取已初始化的 `~/.dsh/profiles/desktop/package.json`。不使用 npm CLI、不安装或升级客户端、不清理其他安装。
2. 按仓库规则核验 Python 3.12+、mise 和 uv。脚本复用同步工具已有的 PyYAML 6.x，通过 uv 隔离运行，不修改依赖清单或全局环境。先执行只读预检，将路径替换为实际安装位置：

   ```powershell
   uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe" --check-only
   ```

3. 用户明确要求同步 / 刷新桌面版，即授权本次产品内容复制及 desktop profile 中的专属 Skill provider 配置。预检通过后执行同一命令并去掉 `--check-only`；仅要求检查时结束。自动匹配本入口不构成全局写入授权。本 Skill 不提交、推送或执行其他客户端同步。
4. 脚本用桌面版自带的 Electron 与 Skill provider 在隔离上下文中读取每项 Skill，核对清单、路径和调用策略；不按版本号拦截，实际加载或校验失败时停止。不启动 Host、模型、SSH 或子代理。
5. 完整产品目录存入 `~/.dsh/marketplaces/agent-marketplace/releases/<内容摘要>/plugins/`；桌面版 `cordis.patch.yml` 仅新增 / 刷新带标记的独立 `agent-marketplace-skills` provider，指向各包 `skills/`。它不覆盖现有 Skill provider、默认根目录、模型、权限或 MCP。同名用户 Skill、手改快照、配置并发修改、重定向路径或同步锁冲突时停止，保留原有配置。已有 provider 的禁用状态保留；旧内容快照保留，不自动删除用户文件。
6. 报告版本、产品与 Skill 数量、实际快照位置、启用状态及未完成项。请用户重开桌面版确认 `/vue`、`/am-config`、`/dev-auto` 等入口；隔离原生读取不等于当前桌面会话已加载，也不证明真实模型或委派流程已运行。

`--dsh-home` 可显式指定数据根，默认为 `DSH_HOME` 或 `~/.dsh`。本同步采用 dsh 原生文件系统 Skill provider，产品分类保留在磁盘目录中，不注册五个 npm 扩展。自有流程见随包 `personal-dev/references/dsh.md` 与 `agent-manager/references/dsh.md`。
