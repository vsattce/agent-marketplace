# 项目级 Agent 规则

本仓库是长期维护的个人 Skill / Plugin Marketplace。

## 默认工作流程

1. **小问题小改与 Superpowers 调用：** 按全局规则根据任务风险与影响选择快速、标准或深入模式。边界明确的小问题和小改动按快速模式处理，只做必要分析、最小改动和针对性验证。Superpowers 及其 Skills 默认不自动调用，只有用户明确手动指定时才调用；即使指定，也按任务规模和风险选择必要步骤，不为简单任务扩展完整流程。

2. **指定后的流程选择：** 用户明确指定使用 Superpowers 或某个 Superpowers Skill 后，可按任务类型、风险和依赖关系组合适用流程：新功能和行为变更使用 `brainstorming` 明确需求与设计；多步骤实现使用 `writing-plans`，再按任务依赖和当前工具能力选择 `subagent-driven-development` 或 `executing-plans`。Bug 和异常行为使用 `systematic-debugging` 定位原因；代码实现与修复按任务规模使用 `test-driven-development`。隔离开发、代码审查和分支收尾按对应 Skill 的触发条件处理；完成声明前使用 `verification-before-completion` 核对证据。

3. **深度匹配任务：** 按风险、影响和不确定性控制读取范围、计划、产物与验证深度，不机械执行全部 Superpowers Skills。适用 Skill 要求的确认、审查和验证步骤按其触发条件执行；纯文案、文档、只读检查和常规 Git 操作不强制套用完整开发链。用户已明确的目标、取舍与授权不重复询问。

4. **手动入口与授权：** `am-config`、`personal-dev` 等仅手动调用的 Skill 仍须用户显式调用，不因其他 Skill 流程而自动触发。显式调用的 Skill 规定只读、不提交或不推送时，按该次调用边界执行；用户另有明确授权时以用户要求为准。任何 Skill 不扩大任务范围或文件系统、运行时、客户端配置及外部服务权限。

5. **客户端与可用性：** Codex / Claude Code 只使用各自当前会话实际可用的 Skill、工具和入口，不把磁盘文件或安装缓存当作已加载。所需能力缺失时说明缺项及受影响步骤，不自行安装、修改全局配置或声称新规则已在当前会话热加载。

## 仓库维护规则

1. **定位与客户端：** 当前仅支持 Claude Code 和 Codex，其他客户端暂不适配或维护。业务流程和 Skill 正文可共享，manifest、Skill 发现、项目配置、工具调用及客户端行为按 Harness 实际能力区分；双端修改时检查双方入口、加载、手动调用策略、随包资源和直接受影响行为。

2. **产品与开发工具边界（repository development tooling）：** .agents/skills/ 中的 Superpowers、项目 upgrade、Claude Code plugin 开发 Skill 及未来项目级开发 Skill，.agents/plugin-dev/ 中的官方参考快照，以及项目 MCP 与 Codex / Claude 开发辅助配置默认只服务本仓库维护，不属于 Marketplace 产品。除非用户明确要求，不把它们注册到 .agents/plugins/marketplace.json、.claude-plugin/marketplace.json、sources.yaml 或对外安装目录，也不计入 Plugin / Skill 数量；README 保留 Superpowers 不计数说明。

3. **来源与自有内容：** sources.yaml 管理第三方来源，scripts/sync.py 同步快照并把实际结果记录到 sources.lock.json；上游快照不顺手修改，内容变化通过来源、ref、upstream 或同步流程引入。agent-manager、personal-dev、项目 upgrade、manifests、自有脚本与测试由本仓库直接维护，不新增 ownership 系统。

4. **工作范围与环境：** 仅修改当前仓库和任务授权内容，先检查并保留用户已有改动。无明确授权不修改用户级客户端配置、全局 Plugin / Skill / MCP、系统环境或全局运行时，也不操作其他项目；环境不满足时报告原因，不自行修复全局环境。

5. **最小变更：** 只解决当前需求；直接相关问题可一并修复，无关问题仅报告，不顺手重构或扩建基础设施。

6. **验证：** 复用现有 unittest，按变更运行 agent-manager、personal-dev、sync、Codex / Claude loader、项目配置或 manifest 对应测试；影响范围大或不明时再扩大验证。默认执行 git diff --check。真实客户端测试只用仓库已有显式开关和隔离 fixture，不改日常全局配置。

7. **文档与入口：** 项目能力、配置、用法、支持范围或维护流程变化时，最小范围同步 README 和直接相关文档。不新建重复 Skill、modern-python Skill 或协作、发布、CI 基础设施。CLAUDE.md 只导入 @AGENTS.md；不复制第二份项目规则。

8. **文档工具：** 近期变化、版本敏感或不确定的行为优先查当前官方资料或已有真实测试；稳定的本地小改动无需每次查文档。OpenAI Docs MCP 用于 Codex / OpenAI plugin、MCP、Skill 与配置行为；Claude Code plugin 行为以官方文档及 `.agents/plugin-dev/upstream/` 中固定版本的参考为准；Context7 用于外部库、框架、SDK、CLI 的 API、配置格式或版本差异。两者均按需调用，复用本任务结果；不可用时查官方网页，查询不发送凭据、私有源码或会话内容。

9. **Git 收尾：** 本仓库使用 Gitee 和 GitHub 双远端：`origin` 指向 `git@gitee.com:vsattce/agent-marketplace.git` 并作为当前分支跟踪远端，`github` 指向 `git@github.com:vsattce/agent-marketplace.git`。普通开发任务在必要验证和 diff 检查后，仅暂存任务文件，以 Conventional Commits 提交；推送时优先推送 `origin` 的当前分支，Gitee 成功后再推送 `github` 的同名分支。Gitee 推送失败时按常规 Git 规则处理并如实报告；GitHub 推送失败可暂缓，不回滚 Gitee、不阻塞任务完成，并报告失败状态。显式调用的管理、只读或审查 Skill 规定不提交或不推送时，遵守该次调用边界，用户另有明确授权时以用户要求为准。禁止 force push。汇报变更、测试、分支、提交哈希、两个远端的推送状态及未验证的客户端。

10. **Skill 描述与展示：** 本仓库自有 Skill（含项目级开发 Skill 及客户端入口）的 `SKILL.md` frontmatter `description` 统一使用中文，按“中文名称＋用途＋调用条件”编写，保留适用范围、只读与手动调用边界及必要技术关键词。`name` 保持稳定的英文调用标识；Codex 的 `agents/openai.yaml` 中 `display_name`、`short_description` 同样使用中文，并与共享描述含义一致。第三方上游快照遵循来源与同步规则，不为本地化直接修改。

## 任务产物目录

- 临时同步、测试和任务日志按需放入 `.agent-tmp/sync/<run-id>/`、`.agent-tmp/tests/<run-id>/`、`.agent-tmp/tasks/<task-id>/`，由 Git 忽略。测试进程需要 `TMP` / `TEMP` 时，只指向本次测试运行目录。
- 委派任务仅在需要跨步骤恢复或保留验收证据时使用 `docs/personal-dev/tasks/<task-id>/`；设计、计划、进度和验收记录按需创建，普通小任务不强制建文档。
- 增强审查报告默认写入 `docs/personal-dev/reviews/<review-id>/report.md`，长审查的轻量进度记录与报告同目录。审查只写报告和必要进度记录，不自动提交或推送。
- 远端诊断默认在聊天中汇报，只有用户要求保存时写入 `docs/personal-dev/runtime/<diagnostic-id>/report.md`。`dev-simplify` 不要求文档，`am-conflict` / `am-update` 不创建文件。
- ID 使用用户时区的日期、时间和主题；冲突追加唯一后缀且不覆盖。目标项目规则和用户指定位置优先。`am-config` 的目标旁 `.am-config-*` 原子替换临时文件与 `.configure-project.lock` 保持原位。
