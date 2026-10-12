# 任务产物目录规范

用户已审阅并明确授权执行聊天中的目录评估方案，指定 dev-delegate 与 gpt-6-luna，要求兼容 Codex 和 Claude Code。本文件记录已确认边界，不新增待批准设计。

## 目标与目录

- 临时产物集中于项目 `.agent-tmp/sync/<运行ID>/`、`.agent-tmp/tests/<运行ID>/`、`.agent-tmp/tasks/<任务ID>/`，按需创建并由 Git 忽略。
- 委派开发的必要长期记录使用 `docs/personal-dev/tasks/<任务ID>/`，设计、计划、进度、验收仅在实际需要时生成。
- 增强审查的报告使用 `docs/personal-dev/reviews/<审查ID>/report.md`，长审查的 progress.md 与报告同目录；保留原有只读、仅报告可写、不自动 commit/push 的边界。
- 远端诊断默认聊天输出，仅明确要求保存时使用 `docs/personal-dev/runtime/<诊断ID>/report.md`。
- dev-yagni/dev-simplify 不强制生成文件；am-conflict/am-update 不新增写入；am-config 不新增报告目录。
- 小任务不强制建文档目录；ID 使用用户时区日期/时间/主题，冲突追加唯一后缀，不覆盖文件。目标项目明确目录规则和用户指定位置优先。

## 实现边界

同步脚本保持 sources/lock 契约、同文件系统暂存、先校验后发布及失败恢复；只改变临时父目录。检查新目录的规范路径和 symlink/junction 边界，不通过重定向写出仓库。

同步、配置和两端原生加载测试的项目内临时目录归入 tests 命名空间；测试 TMP/TEMP 仅在测试进程指定到本次运行目录，不指向仓库根。不扩建通用运行平台。

插件源码、发现目录和手动调用策略保持现状，客户端相关共享资源随插件打包。CLAUDE.md 仅保留 @AGENTS.md。第三方和 Superpowers 上游快照、sources/lock、官方参考快照不修改。

am-config 的目标旁 `.am-config-*` 原子写入临时文件及历史 `.configure-project.lock` 不迁移。原生工作树使用工具返回的路径，不强行集中到临时根目录。

AGENTS.md、README、usage、maintenance 和直接受影响 Skill/模板同步说明。personal-dev 如需发布版本递增，按既有 Codex manifest/catalog 一致性与 Claude 无 version 策略执行。

## 本地历史文件整理

原主检出的五个 docs/reviews 未跟踪文件属于既有用户内容。按审查/修复任务归档，不自动提交。完整原始测试日志进入临时任务目录；报告的现有文件链接更新到归档位置，事实与历史结论保留。移动前核验准确路径、归属、文件哈希和目标不存在，迁移后核验。

两个已确认的根目录 .skill-sync-* 任务目录归入 `.agent-tmp/tasks/`，保留内容，不删除。历史 docs/superpowers 保留原位置和历史记录。

## 验收

有效回归覆盖临时目录布局、唯一性、成功/失败后的清理、同步原有回滚和被重定向临时目录拒绝；两端包装及隔离原生加载维持通过。原子配置临时文件和锁的行为不变，报告型 Skill 不扩大写入或 Git 权限。真实加载器以现有 opt-in fixture 执行，不调用真实模型或改日常客户端配置。
