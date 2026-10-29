# FastAPI 与工程工具历史设计

## 授权与目标

用户已确认增加以下三个 Skill，要求不过度工程化，先明确 spec / plan，再由 `gpt-6-luna` 子代理实现与独立验收。用户已授权文档完成后继续执行，无需再次等待设计或计划批准。按项目规则由主模型完成验证、提交和推送当前分支。

| 入口 | Plugin | 调用策略 | 内容维护 |
| --- | --- | --- | --- |
| fastapi | backend-dev | 任务匹配 / 手动 | 第三方原样快照，纳入 upgrade |
| docker-build-strategies | engineering-tools（工程工具，新建） | 任务匹配 / 手动 | 第三方原样快照，纳入 upgrade |

支持 Codex 与 Claude Code，两端共享内容与资源，使用各自真实可用的原生工具。项目级开发工具不计入产品。

## 第三方来源与升级

- FastAPI：官方 `fastapi/fastapi`，路径 `fastapi/.agents/skills/fastapi`，跟随 `master`。
- Docker：官方 `docker/skills`，路径 `skills/docker-build-strategies`，跟随 `main`。
- 以上来源加入 `sources.yaml`，实际 commit 和同步时间由现有脚本写入 `sources.lock.json`。完整保留 Skill 目录、引用资料、脚本、资产和许可证，不手改上游正文或为了本地化增加上游未提供的 metadata。
- `scripts/sync.py` 的 managed 白名单仅增加明确的新分类 `engineering-tools`，保留对未知分类、自有 Plugin、manifest 与重定向目录的拒绝，以及失败恢复、幂等和许可证规则。
- `.gitattributes` 为新分类的快照与许可证增加 `-text`，保持原始字节。
- 复用既有 `$upgrade` / `/upgrade` 与 `am-update`，不新增升级入口、后台任务或更新框架。
- 首次导入只增加这两项；现有 13 项快照、来源、ref 与 lock 记录保持原状。可以在本次导入命令中让既有 fetch 对旧来源使用 lock commit，不持久修改其分支策略。以后正常 upgrade 按 sources 的真实 ref 查询并升级全部第三方项。
- 第三方正文中的较新 API 和工具建议服从使用项目的版本、依赖与明确要求；不借安装 Skill 升级运行时或替换项目技术栈。

## Plugin 与展示

engineering-tools 沿用现有便携 `plugin.json`、Claude `.claude-plugin/plugin.json` 和两端 Marketplace 注册形式，初期只包含 Docker 构建 Skill。定位为跨技术栈的构建、部署、脚本和工程辅助，不建立额外管理层。

backend-dev 展示增加 FastAPI；engineering-tools 初始版本 1.0.0，backend-dev 1.1.0。Claude manifest 继续采用既有不写 version 的策略。

## 验收

- sources / lock 新增准确两项；旧项与快照不变。证明新分类支持同步、重复同步无差异、上游变化更新、资源与许可证复制，失败可恢复，自有内容不受影响。
- 相关文档、安装列表、调用示例、描述与数量同步，历史记录保留其当时版本和数量。
- 基线工作区干净，HEAD `43f2cb6`，当前 main。旧名称的忽略缓存目录属于已有本地状态，保留；涉及 Skill 枚举的测试按实际 `SKILL.md` 识别入口，不将缓存当作 Skill。已有手动策略测试的英文固定句断言与中文正文不符，按真实 frontmatter / policy 核验，不改范围外 Skill 正文。

### 实测补充：Codex 长正文注入

初始验收拟核对单次请求包含完整正文。独立验收在当前 Codex CLI `0.162.0-alpha.17.2` 的隔离 fixture 中确认：两个第三方 Skill 安装文件均与完整源快照逐字节相同，但显式调用发给 provider 的内容为源 `SKILL.md` 前 8,000 个 UTF-8 字节，外加包装换行；不含正文尾部，也没有截断提示。此处是当前 Harness 的实测行为，不能由 Marketplace 修改上游内容来消除；单次全文注入改为如实记录限制。

这与[官方渐进加载说明](https://learn.chatgpt.com/docs/build-skills)中“8,000 字符预算只用于初始清单，选中后读取全文”的表述存在差异。本轮没有对客户端实现作进一步归因，也不声称已经验证真实模型主动续读剩余文件。Claude fixture 继续检查完整正文。

## 资料

- [FastAPI 官方 Skill](https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md)
- [Docker 官方 Skill](https://github.com/docker/skills/blob/main/skills/docker-build-strategies/SKILL.md)
- [OpenAI Skill metadata](https://developers.openai.com/plugins/deploy/submission-errors#skill-agent-metadata-errors)
- Claude 入口复用本仓库已固定的 `.agents/plugin-dev/upstream/skills/plugin-structure/` 指导及现有真实 loader fixture。
