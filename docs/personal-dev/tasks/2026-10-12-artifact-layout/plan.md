# 任务产物目录规范实施计划

> **For agentic workers:** 用户已明确授权执行并选择 personal-dev:dev-delegate、gpt-6-luna。一个干净上下文的 gpt-6-luna / xhigh 编码，另一个 gpt-6-luna / max 独立验收；主模型整体检查、本地主检出归档、交付、提交并推送 main。子代理禁止派生、commit/push。采用已确认执行方式，不再次等待批准。

**Goal:** 集中临时与长期任务产物，兼容两端并保留项目和 Skill 权限契约。

**Architecture:** 小范围调整现有脚本、测试 fixture、文档和 Skill 引用；personal-dev 共享简短的 references/artifacts.md。保持现有插件、入口、来源和原子配置文件结构。

**Tech Stack:** Python >=3.12（mise 当前 3.12.13）、uv、unittest、PowerShell、Codex/Claude 隔离加载器。

**Spec:** [design.md](design.md)

## Global Constraints

- 仅修改当前仓库任务内容；保留主检出五个未跟踪用户文件，归档后仍不自动提交。
- 不改第三方快照、Superpowers 正文、sources/lock、全局配置、运行时或 PATH。
- .am-config-* 与 .configure-project.lock 保持原位；不更改项目 Plugin 配置契约。
- Git 当前 main，基线 675b0f832b7b2df45e5b9ee0906fd33d55c21f0d；最终非强制推送 origin/main。

## Review Focus

1. 新临时父目录被 symlink/junction 或普通文件占用时拒绝越界，原快照与 lock 保留。
2. 同步成功和失败仅清理当次目录，重复运行不覆盖另一个任务的临时证据。
3. 两端安装后能读取随包 artifacts.md，跨项目以目标项目规则/用户位置为准，不使用安装缓存作为输出根。
4. 审查默认位置变化不引入修改 .gitignore、源码、配置或自动 Git 操作；诊断默认仍为聊天输出。
5. 测试临时目录与 TMP/TEMP 在当前运行内集中，原生 Codex/Claude 的隔离配置不落入日常全局。

## Task 1：实现与针对性验证

- [x] 先添加有效失败回归，验证新布局、唯一性、清理、重定向拒绝；复用已有同步回滚测试。
- [x] 修改 scripts/sync.py、相关 tests fixture 和 .gitignore；原有配置原子文件及锁不变。
- [x] 添加 personal-dev/references/artifacts.md，按实际需要修改 dev-delegate/dev-review/dev-runtime-check 及必要的其他自有 Skill 引用、roles/report-template。
- [x] 同步 AGENTS.md、README、docs/usage.md、docs/maintenance.md、项目 upgrade/claude-plugin-dev 的直接相关目录说明；personal-dev 版本 0.6.1，Claude manifest 继续无 version。
- [x] 定向 unittest、git diff --check；记录真实命令、数量、未验证项。不为纯文案建立镜像断言测试。

## Task 2：独立验收、主检出交付与归档

- [x] 主模型派独立 gpt-6-luna / max 读取实际累计差异、新文件和验证证据；需求和质量 PASS，无阻塞，修复计数 0/2。主模型整体检查通过。
- [x] 以显式任务文件差异安全交付原主检出，26 个文件比对与工作区字节一致，保留既有用户内容；整体检查将在独立验收后完成。
- [x] 主模型核验路径/哈希，将旧临时任务目录及五个本地报告/日志归档，并修正本地报告链接；旧用户文件不进入任务提交。自动审批拒绝删除旧空目录，已记录。
- [x] 在普通主检出执行必要完整 unittest，并用现有 opt-in 同时验证 Codex/Claude 隔离加载；160 项通过，所有临时环境变量仅进程级。
- [x] 更新进度和验收证据，核对明确任务文件清单，保留历史未跟踪报告。

Git 收尾在验收记录写入后执行：仅暂存任务文件，检查暂存差异，Conventional Commit、push origin/main、核验同步，并按原生工具归档隔离工作区。实际提交与推送结果以最终汇报为准。
