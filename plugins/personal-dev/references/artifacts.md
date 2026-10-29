# 任务产物位置

按需保存任务产物，并以当前目标项目规则和用户指定位置为准。使用安装缓存或本 Skill 所在目录时，不能将其当作目标项目的输出根目录。

## 需求与计划

- `docs/personal-dev/specs/<task-id>-design.md`：dev-prepare / dev-auto 共用的 SPEC。
- `docs/personal-dev/plans/<task-id>.md`：对应 PLAN，引用上述 SPEC；单任务也保存两个文件。prepare 确认后只交接，auto 自动检查通过后直接交同包执行器；就绪和消费规则见 [准备与消费契约](preparation.md)。

采用与 Superpowers 相同的分层：`docs/` 保存需求与计划，插件专属隐藏目录保存执行现场。需求与计划默认保留，可随项目版本管理，不要求 Git 忽略，也不自动提交；执行完成后的临时清理不删除它们。

## 临时执行现场

- `.personal-dev/sdd/<task-id>/progress.md`：仅确需并行调度、复杂依赖、长时恢复或只读 PLAN 裁决记录时建立的进度 ledger；普通少量串行任务默认不创建，在可写 PLAN 简记进度。主模型独占写入；恢复核对文件、代码、证据与原生代理状态。中断、失败或阻塞保留，全部验收、整体检查与已授权收尾完成后仅清理本次执行目录；细则见 [任务编排与进度恢复](../skills/dev-delegate/references/orchestration.md)。
- `.personal-dev/sdd/<task-id>/`：按需保存交接材料、短期日志、原始测试输出及临时证据，与 ledger 共用执行目录；需要长期保留的证据先归档至个人开发记录。
- `.personal-dev/tests/<run-id>/`：隔离验证 fixture 与本次测试进程的临时文件。需要设置 `TMP` / `TEMP` 时，只在该测试进程指向本次运行目录。

派发或验证前确认本次隐藏目录被 Git 忽略。未忽略时，在项目授权内补对应的项目忽略规则；不能修改或无法建立必需记录时，报告限制并停止依赖该目录的步骤。按任务或运行实际需要创建目录。

ID 使用用户时区的日期、时间和主题，同一 SPEC / PLAN 与执行目录共用 task-id；任一对应路径已占用时，整组追加同一唯一后缀，不覆盖已有文件。用户指定文件或恢复既有执行时沿用明确路径与 ID，不按最新时间猜选，不自动搬迁旧文件；旧布局的明确 SPEC / PLAN 仍可消费，恢复时复用其已有 ledger，避免维护两份进度。

## 临时目录清理

- 清理前按[命令与资源契约](execution-resources.md)核对本次测试、构建、浏览器与后台服务均已退出，先释放自身占用，再删除目录；worker 结束或测试出现摘要不等于进程结束。仅为本次创建临时文件时，无需新增进程或登记文件。
- 任务完成后仅清理本次创建的临时目录，遵守各入口的清理时机。删除前核实任务归属、解析后的绝对路径及目录链，确认目标位于当前目标项目允许的本次临时目录内（默认 `.personal-dev/sdd/<task-id>/` 或 `.personal-dev/tests/<run-id>/`），未被 symlink / junction 重定向；不得扩大到整个隐藏根目录、类别目录、`docs/personal-dev/`、项目根目录、父目录、用户目录、其他项目或其他任务。既有执行的临时目录按其原有授权范围处理，不因新默认路径自动迁移或删除。
- Windows / PowerShell 使用独立、简单的普通递归删除命令：`Remove-Item -LiteralPath <已核实的绝对路径> -Recurse -ErrorAction Stop`。禁止 `Remove-Item` 及 `rm`、`ri` 等别名使用 `-Force`（含参数缩写），不与其他含 `-Force` 的命令拼接在同一 Shell 调用中。
- 因占用、只读、权限或执行策略拒绝而删除失败时，停止清理、保留目录，在最终结果报告路径及原因；除非残留影响实际功能或测试正确性，否则不判定开发任务失败。不得继续强制删除，或改用 `cmd /c rd /s /q`、Python `shutil.rmtree`、其他 Shell 包装器规避检查；不得为清理修改全局 Codex 安全策略、用户级配置或系统权限。

## 个人开发记录

- `docs/personal-dev/tasks/<task-id>/`：仅当确需长期保留复杂任务记录或验收证据时创建，不重复复制 specs / plans 中的需求与计划。多任务恢复使用临时 ledger；持久证据由 ledger 引用，不维护重复的进度状态。既有目录中的 SPEC / PLAN 继续有效。
- `docs/personal-dev/reviews/<review-id>/report.md`：仅在用户明确要求保存增强审查结果且未指定位置时使用；默认在聊天中输出，不创建审查目录。要求保存且长审查确需中断恢复时，将 `progress.md` 放在报告同目录。增强审查只写获准保存的报告及必要的轻量进度记录，不修改源码、配置或 Git 状态，也不自动提交或推送。
- `docs/personal-dev/runtime/<diagnostic-id>/report.md`：仅在用户明确要求保存远端诊断结果时创建；默认在聊天中汇报，不落盘。

所有持久目录均按需创建。ID 由用户时区的日期、时间和主题组成；冲突时追加唯一后缀，不覆盖已有文件。需要的文件无法写入时，按对应 Skill 的阻塞与报告规则处理。

## 其他入口

- `dev-simplify` 不要求创建任务文档。
- `am-config` 隔离验证默认使用 `.agent-manager/tests/<run-id>/`，按其项目编辑约定隔离、忽略与清理。
- `am-config` 的目标旁 `.am-config-*` 原子替换临时文件和 `.configure-project.lock` 保持原位，继续遵守其现有事务与并发约定。
