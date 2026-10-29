---
name: sync-dsh
description: 同步 dsh 桌面版 Skills：用于用户要求检查或同步本仓库产品插件内容到已安装的 DeepSeek Harness 桌面版；保留资源与手动调用边界，排除仓库开发工具。
---

# 同步产品内容到 DeepSeek Harness 桌面版

仅用于当前 agent-marketplace 仓库。Codex 使用 `$sync-dsh`；Claude Code / agy 使用 `/sync-dsh` 项目入口。读取 `.agents/plugins/marketplace.json` 中的产品，只同步五个产品包的共享 Skills 与资源；`am-context` 仅 Codex，仓库开发 Skills、Superpowers、MCP 和本入口不导出。

1. 检查 Git 状态，保留用户改动；确认用户指定的是已安装的 **桌面版**及其 `DeepSeek Harness.exe`。数据根 `<dsh-home>` 按 `--dsh-home`、`DSH_HOME`、`~/.dsh` 的优先级选定，读取其 `profiles/desktop/package.json`。不使用 npm CLI、不安装或升级客户端、不清理其他安装。
2. 按仓库规则核验 Python 3.12+、mise 和 uv。执行命令前读取[命令与资源契约](../../../plugins/personal-dev/references/execution-resources.md)，确认本次 Python / Electron 隔离进程退出后才重试或清理；用户的 DeepSeek Harness 桌面进程不属于清理对象。脚本复用同步工具已有的 PyYAML 6.x，通过 uv 隔离运行，不修改依赖清单或全局环境。先执行只读预检，将路径替换为实际安装位置：

   ```powershell
   uv run --python (mise which python) --no-python-downloads --script .agents/skills/sync-dsh/scripts/sync.py --desktop-path "D:\DeepSeek Harness\DeepSeek Harness.exe" --check-only
   ```

3. 用户明确要求同步 / 刷新桌面版，即授权本次产品内容复制及 desktop profile 中的专属 Skill provider 配置。预检通过后执行同一命令并去掉 `--check-only`；仅要求检查时结束。自动匹配本入口不构成全局写入授权。本 Skill 不提交、推送或执行其他客户端同步。
4. 脚本用桌面版自带的 Electron 与 Skill provider 在隔离上下文中读取每项 Skill，核对清单、路径和调用策略；不按版本号拦截，实际加载或校验失败时停止。不启动 Host、模型、SSH 或子代理。
5. 产品先复制到 `<dsh-home>/marketplaces/agent-marketplace/releases/.stage-*/`，完整校验后发布为 `<内容摘要>/plugins/`；复制失败保留暂存路径，不占用最终摘要目录。预检也检查既有目标快照和同步锁。桌面版 `cordis.patch.yml` 仅新增 / 刷新带标记的独立 `agent-marketplace-skills` provider，指向各包 `skills/`，不覆盖其他 provider、默认根目录、模型、权限或 MCP。同名用户 Skill、手改快照、配置并发修改、重定向路径、同步锁或托管块结构冲突时停止，保留原有配置。已有 provider 的禁用状态及旧快照保留，不自动删除用户文件。
6. 预检或同步失败时，先根据错误只读检查相关文件和脚本，确定具体冲突及影响，不只转述错误。用户已明确要求同步时，如确认托管标记内仅多出独立的顶层配置项，且可仅移动结束标记将其完整保留在块外，核对配置未并发变化后执行该修正，再重新预检和同步；其他冲突保留原配置，不绕过保护。仅要求检查时不修改配置。
7. 报告版本、产品与 Skill 数量、实际快照位置、启用状态及未完成项；中断时说明阶段、文件、冲突、保护原因、已完成 / 未执行的操作及解决办法，区分事实与推测，不泄露敏感配置。请用户重开桌面版确认 `/vue`、`/am-config`、`/dev-auto` 等入口；隔离读取不证明当前会话已加载或真实模型、委派流程已运行。

指定自定义数据根时，在预检和同步命令中使用相同的 `--dsh-home <实际目录>`。本同步采用 dsh 原生文件系统 Skill provider，产品分类保留在磁盘目录中，不注册五个 npm 扩展。自有流程见随包 `personal-dev/references/dsh.md` 与 `agent-manager/references/dsh.md`。
