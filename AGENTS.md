# 项目级 Agent 规则

本仓库是长期维护的个人 Skill / Plugin Marketplace。

1. **定位与客户端：** 当前仅支持 Claude Code 和 Codex，其他客户端暂不适配或维护。业务流程和 Skill 正文可共享，manifest、Skill 发现、项目配置、工具调用及客户端行为按 Harness 实际能力区分；双端修改时检查双方入口、加载、手动调用策略、随包资源和直接受影响行为。

2. **产品与开发工具边界（repository development tooling）：** .agents/skills/ 中的 Superpowers、项目 upgrade、Claude Code plugin 开发 Skill 及未来项目级开发 Skill，.agents/plugin-dev/ 中的官方参考快照，以及项目 MCP 与 Codex / Claude 开发辅助配置默认只服务本仓库维护，不属于 Marketplace 产品。除非用户明确要求，不把它们注册到 .agents/plugins/marketplace.json、.claude-plugin/marketplace.json、sources.yaml 或对外安装目录，也不计入 Plugin / Skill 数量；README 保留 Superpowers 不计数说明。

3. **来源与自有内容：** sources.yaml 管理第三方来源，scripts/sync.py 同步快照并把实际结果记录到 sources.lock.json；上游快照不顺手修改，内容变化通过来源、ref、upstream 或同步流程引入。agent-manager、personal-dev、项目 upgrade、manifests、自有脚本与测试由本仓库直接维护，不新增 ownership 系统。

4. **工作范围与环境：** 仅修改当前仓库和任务授权内容，先检查并保留用户已有改动。无明确授权不修改用户级客户端配置、全局 Plugin / Skill / MCP、系统环境或全局运行时，也不操作其他项目；环境不满足时报告原因，不自行修复全局环境。

5. **最小变更：** 只解决当前需求；直接相关问题可一并修复，无关问题仅报告，不顺手重构或扩建基础设施。

6. **验证：** 复用现有 unittest，按变更运行 agent-manager、personal-dev、sync、Codex / Claude loader、项目配置或 manifest 对应测试；影响范围大或不明时再扩大验证。默认执行 git diff --check。真实客户端测试只用仓库已有显式开关和隔离 fixture，不改日常全局配置。

7. **文档与入口：** 项目能力、配置、用法、支持范围或维护流程变化时，最小范围同步 README 和直接相关文档。不新建重复 Skill、modern-python Skill 或协作、发布、CI 基础设施。CLAUDE.md 只导入 @AGENTS.md；不复制第二份项目规则。

8. **文档工具：** 近期变化、版本敏感或不确定的行为优先查当前官方资料或已有真实测试；稳定的本地小改动无需每次查文档。OpenAI Docs MCP 用于 Codex / OpenAI plugin、MCP、Skill 与配置行为；Claude Code plugin 行为以官方文档及 `.agents/plugin-dev/upstream/` 中固定版本的参考为准；Context7 用于外部库、框架、SDK、CLI 的 API、配置格式或版本差异。两者均按需调用，复用本任务结果；不可用时查官方网页，查询不发送凭据、私有源码或会话内容。

9. **Git 收尾：** 必要验证和 diff 检查后，仅暂存任务文件，以 Conventional Commits 提交并推送当前分支；用户明确要求不提交或不推送时遵从。禁止 force push。远端收到提交才算同步；失败如实报告，并汇报变更、测试、分支、提交哈希、推送状态及未验证的客户端。

10. **Skill 描述与展示：** 本仓库自有 Skill（含项目级开发 Skill 及客户端入口）的 `SKILL.md` frontmatter `description` 统一使用中文，按“中文名称＋用途＋调用条件”编写，保留适用范围、只读与手动调用边界及必要技术关键词。`name` 保持稳定的英文调用标识；Codex 的 `agents/openai.yaml` 中 `display_name`、`short_description` 同样使用中文，并与共享描述含义一致。第三方上游快照遵循来源与同步规则，不为本地化直接修改。

## 任务产物目录

- 临时同步、测试和任务日志按需放入 `.agent-tmp/sync/<run-id>/`、`.agent-tmp/tests/<run-id>/`、`.agent-tmp/tasks/<task-id>/`，由 Git 忽略。测试进程需要 `TMP` / `TEMP` 时，只指向本次测试运行目录。
- 委派任务仅在需要跨步骤恢复或保留验收证据时使用 `docs/personal-dev/tasks/<task-id>/`；设计、计划、进度和验收记录按需创建，普通小任务不强制建文档。
- 增强审查报告默认写入 `docs/personal-dev/reviews/<review-id>/report.md`，长审查的轻量进度记录与报告同目录。审查只写报告和必要进度记录，不自动提交或推送。
- 远端诊断默认在聊天中汇报，只有用户要求保存时写入 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。`dev-yagni` / `dev-simplify` 不要求文档，`am-conflict` / `am-update` 不创建文件。
- ID 使用用户时区的日期、时间和主题；冲突追加唯一后缀且不覆盖。目标项目规则和用户指定位置优先。`am-config` 的目标旁 `.am-config-*` 原子替换临时文件与 `.configure-project.lock` 保持原位。
