---
name: upgrade
description: 升级第三方 Skills：用于升级或同步 agent-marketplace 仓库中 sources.yaml 配置的第三方 Skills，复用现有同步脚本并完成验证、提交和推送；只读版本检查、其他项目依赖升级和 Codex 安装缓存刷新另行处理。
---

# 升级本项目第三方 Skills

Codex 用户调用 `$upgrade`，Claude Code 用户通过 `.claude/skills/upgrade/` 入口调用 `/upgrade`，即执行升级，无需用户手动输入同步命令。两端共用本文件的执行正文；不依赖任何一端专用的委派工具。

同步暂存由脚本保存在项目 `.agent-tmp/sync/<run-id>/` 并在结束时清理。短期命令日志按需放入 `.agent-tmp/tasks/<task-id>/`；只有需要跨步骤恢复或保留验收证据时才创建长期任务记录。路径细则见[任务产物位置](../../../plugins/personal-dev/references/artifacts.md)。

## 确认目标与环境

1. 从本 Skill 所在目录解析 `../../..` 得到仓库根目录。用 `git rev-parse --show-toplevel` 确认当前工作目录属于该仓库，并确认根目录存在 `sources.yaml`、`sources.lock.json`、`scripts/sync.py` 和 `.agents/plugins/marketplace.json`。不匹配时停止，不转向其他仓库。
2. 在仓库根读取 `AGENTS.md`、`sources.yaml` 和同步脚本的 PEP 723 运行时声明；记录 `git status --short` 及已有暂存内容。已有第三方快照或 lock 改动可能被同步覆盖，先确认其用途；保留其他用户改动，提交时只包含本次任务改动。
3. 在仓库根执行以下环境检查，确认 mise 当前 Python、实际 Python 和 `mise which python` 指向的解释器一致，并满足脚本要求（当前 Python 3.12+）：

   ```powershell
   mise current
   python --version
   mise which python
   uv --version
   ```

   环境缺失或版本不匹配时停止，报告检测结果与项目要求，由用户处理。保持现有 mise 配置和运行时，不自行安装或切换解释器。

## 执行升级

环境核对通过后，在仓库根执行一次：

```powershell
uv run --python (mise which python) --no-python-downloads --script scripts/sync.py
```

其他 Shell 使用等效命令，将 `mise which python` 的结果作为 `--python` 的单个参数，保留 `--no-python-downloads`。

- 以 `sources.yaml` 的 repo / path / ref 为准：分支获取该分支最新内容，固定 commit 继续固定。保持既定来源和 ref；改变固定版本需用户明确要求。
- 复用脚本的校验、许可证保留、快照替换、lock 更新与失败恢复。第三方内容按 upstream 原样同步，自有 Plugin、项目 Skill、manifest 和全局安装配置保持原状。
- 退出码非零时停止，说明失败阶段与原因，检查实际差异；不提交失败结果，不循环重试，不自行修补第三方内容绕过校验。

## 验证与交付

1. 对比升级前后的状态、`git diff --stat`、`git diff -- sources.lock.json` 和同步输出。核对每项 commit 与配置 ref 一致，新增 / 修改 / 移除文件属于配置的第三方快照或许可证，并检查 README 的来源说明是否需要更新。脚本保留的 unlisted 项单独报告，保持原状。
2. 有升级差异时，运行同步相关测试和 `git diff --check`：

   ```powershell
   uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" python -B -m unittest discover -s tests -p test_sync.py -v
   git diff --check
   ```

   验证失败时停止 Git 收尾，报告原因和未验证项；零差异时报告已是配置 ref 的当前版本，无需制造提交或重复运行同步。
3. 按当前项目 `AGENTS.md` 完成 Git 收尾；当前规则默认提交并推送当前分支。逐项暂存本次升级文件及必要 README 改动，检查暂存差异，使用准确的 Conventional Commit，例如 `chore(skills): 同步第三方 Skill 快照`。保留既有无关暂存内容；若无法隔离提交，先解决范围问题。用户明确不提交或不推送时遵从用户要求。推送失败如实报告，禁止强推。
4. 简要汇报实际更新项、固定版本保持情况、验证结果、分支与提交哈希或无差异状态。明确仓库已同步不代表当前客户端的安装副本已刷新；仅在用户另行要求刷新时处理安装副本。
