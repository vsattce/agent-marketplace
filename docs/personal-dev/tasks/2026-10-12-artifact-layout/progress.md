# 目录规范整理进度

- 状态：ACCEPTED；实现、主检出验证、独立验收和主模型整体检查通过。Git 收尾在本记录写入后执行，提交与推送结果以最终汇报为准。
- 基线：main / 675b0f832b7b2df45e5b9ee0906fd33d55c21f0d。
- 主检出：E:/WorkSpace/agent-marketplace；隔离工作区：C:/Users/ASUS/.codex/worktrees/task-artifact-layout/agent-marketplace。
- 原有用户内容已归档：审查报告/进度至 docs/personal-dev/reviews/2026-10-11-112236-project-review/，修复报告/进度至 docs/personal-dev/tasks/2026-10-11-review-fixes/，原始日志至 .agent-tmp/tasks/2026-10-11-review-fixes/；4 个 Markdown 保持未跟踪，不进入任务提交。两个旧任务目录移入 .agent-tmp/tasks/，25 个文件逐一核验哈希。5 个本地文件在修正链接前也核验原始哈希。
- 模型预检：select_models.py READY，用户确认 gpt-6-luna；编码 xhigh，独立验收 max。主模型精确 ID 未确认，未根据自报猜测默认型号。
- 原始基线验证：test_sync.py 21/21；test_personal_dev_packaging.py 3/3，均 OK。
- 环境：mise Python 3.12.13 / uv 0.12.3，符合 Python >=3.12。
- 修复计数：0/2；独立验收 /root/accept_artifact_layout，gpt-6-luna / max，干净上下文，只读，需求 PASS、质量与正确性 PASS，无阻塞项。
- 编码代理：/root/implement_artifact_layout，gpt-6-luna / xhigh，干净上下文。验证证据由代理回传，最终保存在 acceptance.md。
- 原生工作区位于受保护 .codex 路径；需要真实项目配置写入的测试在普通主检出运行，不放宽路径保护。
- 编码定向验证：sync 25、temp_paths 4、am-config 41、personal-dev 包装 3，共 73 项 OK；8 项新增行为回归均记录实际 RED/GREEN。
- 主检出完整验证：2026-10-12，启用 AGENT_MANAGER_CODEX_TESTS=1 / AGENT_MANAGER_CLAUDE_TESTS=1，160 项 / 55.526 秒 / OK，退出 0、无跳过。mise Python 3.12.13；Codex 0.162.0-alpha.17.2 / Claude 2.1.296。TMP/TEMP 仅本进程指向 .agent-tmp/tests/validation-7d22691bc8f643fab1645400e6aea62a。
- 日常 Codex/Claude 配置存在性与 SHA256 基线核验一致。测试只捕获加载请求并拒绝推理，不证明真实模型执行 Skill。
- 证据：.agent-tmp/tasks/2026-10-12-artifact-layout/full-validation.log、coding/、archive-task-hashes.json、archive-report-hashes.json（本地忽略，不提交原始日志）。
- 归档限制：批量移动命令被自动审批拒绝，已改为明确 LiteralPath 逐项移动并核验成功。删除旧 docs/reviews 空目录的显式非递归命令仍被自动审批拒绝（仅返回 blocked by policy）；空目录保留，不重试。
- 主模型整体检查：已检查全部累计代码与文档差异、新文件、两端入口和随包引用、验证范围及用户原有内容边界，未发现遗漏或范围外修改。最终 git diff --check HEAD 通过；只暂存本任务文件，历史归档 Markdown 不提交。
- 用户补充：旧文件迁移不关键，可自行删除；后续不继续整理旧目录，完成验收和 Git 收尾。
- 完整结论与未验证项见 [acceptance.md](acceptance.md)。
