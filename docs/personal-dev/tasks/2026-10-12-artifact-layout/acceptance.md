# 任务产物目录整理验收

2026-10-12，需求 PASS，质量与正确性 PASS，无阻塞项；主模型整体检查通过。初次实现后未返工，修复计数 0/2。

## 交付结果

- 同步暂存、测试 fixture 和短期任务证据分别集中到 `.agent-tmp/sync/`、`.agent-tmp/tests/`、`.agent-tmp/tasks/`，由 Git 忽略。
- 必要的委派任务记录、增强审查报告和用户要求保存的诊断报告统一使用 `docs/personal-dev/` 下对应目录；小任务不强制建档。
- AGENTS.md、README、使用和维护文档、项目 upgrade/plugin-dev 入口与 personal-dev 共享资源一致。输出以目标项目和用户指定位置为准，不写入安装缓存。
- 同步保持来源、lock、先校验后发布和回滚契约；配置原子临时文件及锁仍在原位。审查、诊断和管理 Skill 的写入与 Git 权限边界未扩大。
- Codex personal-dev manifest 为 0.6.1，Claude manifest 保持无 version；两端沿用已有入口、手动调用策略和共享正文。未刷新日常已安装插件缓存。

## 独立验收与整体检查

编码代理 `/root/implement_artifact_layout` 使用 gpt-6-luna / xhigh；独立验收代理 `/root/accept_artifact_layout` 使用 gpt-6-luna / max。两者使用干净上下文，未派生代理或提交代码。

独立验收核对实际未提交差异、新文件、相关调用点和验证日志，确认唯一运行目录、成功与失败清理、被重定向路径拒绝及原有回滚行为。需求和质量均 PASS，无有证据的阻塞项；证据足够，未重复全量测试。主模型另检查累计实际改动、需求覆盖、两端资源引用、验证范围和范围外内容，结果通过。

## 验证证据

- 原始基线：同步 21 项、personal-dev 包装 3 项通过。
- 编码定向验证：同步 25 项、临时路径 4 项、项目配置 41 项、personal-dev 包装 3 项，共 73 项通过。8 项新增行为回归记录了实际 RED/GREEN。
- 主检出完整验证：160 项，55.526 秒，OK，退出 0，无跳过；同时启用 `AGENT_MANAGER_CODEX_TESTS=1` 和 `AGENT_MANAGER_CLAUDE_TESTS=1`。
- 执行环境：mise Python 3.12.13、uv 0.12.3；Codex 0.162.0-alpha.17.2、Claude Code 2.1.296。运行前已核验项目版本约束与实际解释器。
- `TMP` / `TEMP` 仅对本次测试进程设置到 `.agent-tmp/tests/validation-7d22691bc8f643fab1645400e6aea62a`。日常两端配置的存在性及 SHA256 前后保持一致。
- `git diff --check HEAD` 通过。提交范围排除历史归档报告、原始日志和测试临时目录。

完整测试使用现有隔离开关，在主检出执行：

```powershell
uv run --python (mise which python) --no-python-downloads --with 'PyYAML>=6.0.2,<7' --with 'tomlkit>=0.13.3,<1' python -B -m unittest discover -s tests -v
```

完整原始日志保存在本地 `.agent-tmp/tasks/2026-10-12-artifact-layout/full-validation.log`；定向日志位于同目录 `coding/`。原始日志由 Git 忽略，不随本报告提交。

## 验证边界与归档

两端 opt-in 测试使用隔离 fixture 捕获加载请求并拒绝推理，证明入口及加载行为，不代表真实模型执行 Skill。未进行真实上游网络同步；未单独新增 junction 回归夹具，实现已有明确 junction 检查，实际回归覆盖符号链接和文件占位。

两个旧根目录任务文件夹和五份本地报告/日志已核验原始哈希后归档；报告仅补充归档说明与修正链接，历史 Markdown 仍未跟踪，不进入提交。用户说明旧文件迁移不关键，后续不继续整理旧目录。

旧 `docs/reviews/` 空目录的显式非递归删除被自动审批拒绝，仅返回 `blocked by policy`；目录保留，不重试。此限制不影响 Skill、同步脚本或验收结果。

Git 提交、推送及隔离工作区归档在本报告写入后执行，实际结果见最终汇报。
