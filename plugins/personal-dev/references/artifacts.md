# 任务产物位置

按需保存任务产物，并以当前目标项目规则和用户指定位置为准。使用安装缓存或本 Skill 所在目录时，不能将其当作目标项目的输出根目录。

## 临时产物

- `.agent-tmp/sync/<run-id>/`：同步脚本的暂存与校验文件。同步脚本在成功和失败后都清理本次运行目录。
- `.agent-tmp/tests/<run-id>/`：项目内测试 fixture 与本次测试进程的临时文件。需要设置 `TMP` / `TEMP` 时，只在该测试进程指向本次运行目录。
- `.agent-tmp/tasks/<task-id>/`：短期任务日志、原始测试输出及便于复查的临时证据；它们不代替长期记录。
- `.agent-tmp/dev-delegate/<task-id>/spec.md` / `plan.md`：dev-prepare / dev-auto 共用的需求与执行计划；单任务也保存文件。prepare 确认后保留供用户另行委派，auto 自动检查通过后直接交同包执行器；就绪和消费规则见 [准备与消费契约](preparation.md)。
- `.agent-tmp/dev-delegate/<task-id>/progress.md`：两个及以上开发任务自动建立的临时进度 ledger，含串行依赖；单个简单任务默认不创建，只读 PLAN 确需裁决或恢复记录时按需复用。主模型独占写入，派发前确认 Git 忽略；恢复核对文件、代码、证据与原生代理状态。中断、失败或阻塞保留，全部验收、整体检查与已授权收尾完成后仅清理本次目录；细则见 [任务编排与进度恢复](../skills/dev-delegate/references/orchestration.md)。

按任务或运行实际需要创建目录。ID 使用用户时区的日期、时间和主题；发生冲突时追加唯一后缀，绝不覆盖已有文件。

## 临时目录清理

- 任务完成后仅清理本次创建的临时目录，遵守各入口的清理时机。删除前核实任务归属、解析后的绝对路径及目录链，确认目标位于当前目标项目允许的本次临时目录内（默认上述 `.agent-tmp/<类别>/<本次ID>/`），未被 symlink / junction 重定向；不得扩大到整个临时根目录、类别目录、项目根目录、父目录、用户目录、其他项目或其他任务。
- Windows / PowerShell 使用独立、简单的普通递归删除命令：`Remove-Item -LiteralPath <已核实的绝对路径> -Recurse -ErrorAction Stop`。禁止 `Remove-Item` 及 `rm`、`ri` 等别名使用 `-Force`（含参数缩写），不与其他含 `-Force` 的命令拼接在同一 Shell 调用中。
- 因占用、只读、权限或执行策略拒绝而删除失败时，停止清理、保留目录，在最终结果报告路径及原因；除非残留影响实际功能或测试正确性，否则不判定开发任务失败。不得继续强制删除，或改用 `cmd /c rd /s /q`、Python `shutil.rmtree`、其他 Shell 包装器规避检查；不得为清理修改全局 Codex 安全策略、用户级配置或系统权限。

## 个人开发记录

- `docs/personal-dev/tasks/<task-id>/`：仅当准备 / 委派开发确需长期保留 SPEC / PLAN、复杂任务记录或验收证据时创建，不为普通执行建档。多任务恢复默认使用临时 ledger；持久证据由 ledger 引用，不维护重复的进度状态。
- `docs/personal-dev/reviews/<review-id>/report.md`：增强审查报告的默认位置。长审查需要进度记录时，将 `progress.md` 放在同一目录。增强审查只写报告及必要的轻量进度记录，不修改源码、配置或 Git 状态，也不自动提交或推送。
- `docs/personal-dev/runtime/<diagnostic-id>/report.md`：仅在用户明确要求保存远端诊断结果时创建；默认在聊天中汇报，不落盘。

所有持久目录均按需创建。ID 由用户时区的日期、时间和主题组成；冲突时追加唯一后缀，不覆盖已有文件。需要的文件无法写入时，按对应 Skill 的阻塞与报告规则处理。

## 其他入口

- `dev-simplify` 不要求创建任务文档。
- `am-config` 的目标旁 `.am-config-*` 原子替换临时文件和 `.configure-project.lock` 保持原位，继续遵守其现有事务与并发约定。
