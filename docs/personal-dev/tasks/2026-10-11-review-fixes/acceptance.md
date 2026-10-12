# agent-marketplace 审查问题修复与复验报告

归档说明（2026-10-12）：从原 docs/reviews 目录迁入，保留历史结论，更新已迁移文件的链接；继续作为本地未提交记录。

日期：2026-10-11。状态：COMPLETE；三项修复、独立验收、主代理终审、提交及推送均已完成。

本次只修复原审查确认的三项 P2 问题。生产实现集中于三个既有脚本，补充直接相关回归测试、支持说明和 agent-manager 补丁版本；没有重构配置事务或同步流程，没有修改第三方快照、来源配置、依赖及全局客户端配置。

## 修复结果

| 原问题 | 最小修复 | 复验结论 |
| --- | --- | --- |
| YAML / JSON 重复映射键导致来源漏项 | sync 与 am-update 在本地 sources / lock 解析时拒绝重复键，包括嵌套键、merge 来源内部重复键及重复 `<<`。校验发生在查询、fetch、发布之前，错误不回显键值。 | PASS：错误输入没有网络调用或发布，已有文件保持原字节；合法 alias 显式覆盖与单个 merge sequence 优先级保持。 |
| POSIX 目录竞争可能把配置写入导向项目外 | Plugin 开关编辑器仅在 Windows 运行。CLI、configure 入口和内部 publish 目录守卫拒绝非 Windows，返回 `BLOCKED / PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS`。 | PASS：非 Windows 入口在项目探测及配置读写前拒绝，直接 publish 不创建配置目录。 |
| FIFO 等特殊目标可能阻塞配置读取 | safe_path 拒绝现有既非普通文件也非目录的目标，继续允许目录预检。 | PASS：模拟 FIFO 类型被立即拒绝；原 symlink、junction、hardlink 防护及正常目录用例通过。 |

Windows 限制只适用于 Plugin 开关辅助编辑器。AGENTS.md 编辑、standalone Skill 复制和源码同步没有增加此限制。支持的客户端版本、CLI / stdin / 输出契约、锁、并发检测、原子替换、字节保留及失败恢复保持原有实现。Codex agent-manager manifest 从 0.6.0 升至 0.6.1；Claude manifest 继续采用原有不填写 version 的策略。

实现入口：[sync.py](E:/WorkSpace/agent-marketplace/scripts/sync.py:35)、[check_sources.py](E:/WorkSpace/agent-marketplace/plugins/agent-manager/skills/am-update/scripts/check_sources.py:24)、[configure_project.py](E:/WorkSpace/agent-marketplace/plugins/agent-manager/skills/am-config/scripts/configure_project.py:47)。

## 验证与独立验收

编码代理使用 `gpt-6-luna / xhigh`，独立只读验收使用另一个干净上下文的 `gpt-6-luna / max`。先补有效失败回归，再实现；初次实现期间发现并补齐 merge 节点内部重复键及重复 `<<` 的相邻遗漏。独立验收结论为需求 PASS、质量与正确性 PASS、无确定阻塞项；正式返工轮次 0/2。主代理随后读取全部累计差异及配置读写直接调用路径，整体检查通过。

| 验证 | 实际结果 |
| --- | --- |
| 编码代理定向 unittest | sync 19、agent-manager 13、configure-project 41、configure-project-claude 26，共 99 项通过，四组 exit 0。 |
| 主代理完整 unittest，开启 Codex 与 Claude 隔离开关 | 147 项，54.127 秒，OK，exit 0，零失败、零跳过。 |
| 既有配置行为 | 注释及无关字节保留、幂等、整批拒绝、锁、并发检测、发布失败恢复相关用例通过。 |
| 真实客户端隔离加载 | 两端安装发现、手动入口、personal-dev 显式注入、项目规则入口及 Plugin 项目覆盖验证通过。 |
| 差异与范围检查 | 11 个既有文件，424 行新增、18 行删除；多数新增为回归用例。git diff --check 通过，无第三方快照、依赖或全局配置改动。 |

完整日志：[2026-10-11-review-fixes-tests.log](E:/WorkSpace/agent-marketplace/.agent-tmp/tasks/2026-10-11-review-fixes/full-validation.log)。原审查：[2026-10-11-112236-review.md](E:/WorkSpace/agent-marketplace/docs/personal-dev/reviews/2026-10-11-112236-project-review/report.md)。过程记录：[2026-10-11-review-fixes-progress.md](E:/WorkSpace/agent-marketplace/docs/personal-dev/tasks/2026-10-11-review-fixes/progress.md)。

本轮核验环境为 mise Python 3.12.13、uv 0.12.3、Codex CLI 0.162.0-alpha.17.2、Claude Code 2.1.296。复用既有 uv 工具环境中的 PyYAML 6.0.3 与缓存 tomlkit 0.13.3，没有安装依赖或切换运行时。初次使用裸解释器因缺 PyYAML 未能导入测试；改用已有工具环境后上述测试通过，该导入失败不计入产品缺陷。

完整测试入口为既有 uv 环境的 `python.exe -B -m unittest discover -s tests -v`，同时设置进程 UTF8、规范项目 TMP / TEMP 及 `AGENT_MANAGER_CODEX_TESTS=1`、`AGENT_MANAGER_CLAUDE_TESTS=1`。测试仅使用隔离 CODEX_HOME / CLAUDE_CONFIG_DIR 和 localhost 捕获器。本轮临时目录及九个 Claude 探针叶子文件已清理，原有 `.skill-sync-plugin-dev-task` 保留。

## 验证边界

非 Windows 平台门槛在 Windows 上通过 `os.name` 模拟；FIFO 类型通过模拟 lstat 属性验证。本轮没有在 POSIX 系统运行目录交换或真实 FIFO 实验，因此不能将这些结果表述为 POSIX 运行验收。非 Windows 的 Plugin 开关编辑明确拒绝执行。

真实客户端加载证据覆盖发现、注入和配置行为，不证明每个 Skill 的完整业务流程或模型推理质量。本轮没有连接生产、调用真实模型、查询真实上游更新、同步第三方快照或验证自定义 Windows ACL。

## Git 交付

修复基线：main / b661a673831eb04dc47e8574e8968263b5c5e353。仅提交任务的 11 个代码、测试及必要说明文件；docs/reviews 中的报告和日志作为本地交付材料保留，不混入代码提交。

- 提交：`d9b95c9e13b44aa586fca8faa1dc02cc65b7d163`，`fix!: 拒绝重复来源键并拦截不安全配置目标`。
- 提交正文通过 BREAKING CHANGE 明确 Plugin 开关编辑器的 Windows 平台边界与继续使用方式。
- 推送：`origin main` 成功；随后实时 `git ls-remote` 确认远端 main 已收到同一完整提交。
- 本地与 origin/main 领先 / 落后均为 0；tracked / staged 无剩余差异，只有本地 `docs/reviews/` 未跟踪材料。
- 提交前暂存区与提交后 `git diff --check` 均通过，未使用强推。
