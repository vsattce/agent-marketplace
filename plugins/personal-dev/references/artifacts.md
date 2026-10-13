# 任务产物位置

按需保存任务产物，并以当前目标项目规则和用户指定位置为准。使用安装缓存或本 Skill 所在目录时，不能将其当作目标项目的输出根目录。

## 临时产物

- `.agent-tmp/sync/<run-id>/`：同步脚本的暂存与校验文件。同步脚本在成功和失败后都清理本次运行目录。
- `.agent-tmp/tests/<run-id>/`：项目内测试 fixture 与本次测试进程的临时文件。需要设置 `TMP` / `TEMP` 时，只在该测试进程指向本次运行目录。
- `.agent-tmp/tasks/<task-id>/`：短期任务日志、原始测试输出及便于复查的临时证据；它们不代替长期记录。
- `.agent-tmp/dev-delegate/<task-id>/progress.md`：拆出两个及以上开发任务时自动建立的临时进度 ledger，含串行依赖任务；单个简单任务不创建。主模型独占写入，派发前确认 Git 忽略；恢复时先读取，再核对代码、证据与原生代理状态。中断或阻塞保留，全部验收、整体检查与已授权收尾完成后仅清理本次目录；细则见 [任务编排与进度恢复](../skills/dev-delegate/references/orchestration.md)。

按任务或运行实际需要创建目录。ID 使用用户时区的日期、时间和主题；发生冲突时追加唯一后缀，绝不覆盖已有文件。

## 个人开发记录

- `docs/personal-dev/tasks/<task-id>/`：仅当委派开发确需长期保留设计、复杂任务记录或验收证据时创建，不为普通执行建档。多任务恢复默认使用临时 ledger；持久证据由 ledger 引用，不维护重复的进度状态。
- `docs/personal-dev/reviews/<review-id>/report.md`：增强审查报告的默认位置。长审查需要进度记录时，将 `progress.md` 放在同一目录。增强审查只写报告及必要的轻量进度记录，不修改源码、配置或 Git 状态，也不自动提交或推送。
- `docs/personal-dev/runtime/<diagnostic-id>/report.md`：仅在用户明确要求保存远端诊断结果时创建；默认在聊天中汇报，不落盘。

所有持久目录均按需创建。ID 由用户时区的日期、时间和主题组成；冲突时追加唯一后缀，不覆盖已有文件。需要的文件无法写入时，按对应 Skill 的阻塞与报告规则处理。

## 其他入口

- `dev-simplify` 不要求创建任务文档。
- `am-config` 的目标旁 `.am-config-*` 原子替换临时文件和 `.configure-project.lock` 保持原位，继续遵守其现有事务与并发约定。
