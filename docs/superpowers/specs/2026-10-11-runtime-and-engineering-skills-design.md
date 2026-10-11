# FastAPI、工程工具与远程运行诊断设计

## 授权与目标

用户已确认增加以下三个 Skill，要求不过度工程化，先明确 spec / plan，再由 `gpt-6-luna` 子代理实现与独立验收。用户已授权文档完成后继续执行，无需再次等待设计或计划批准。按项目规则由主模型完成验证、提交和推送当前分支。

| 入口 | Plugin | 调用策略 | 内容维护 |
| --- | --- | --- | --- |
| fastapi | backend-dev | 任务匹配 / 手动 | 第三方原样快照，纳入 upgrade |
| docker-build-strategies | engineering-tools（工程工具，新建） | 任务匹配 / 手动 | 第三方原样快照，纳入 upgrade |
| dev-runtime-check | personal-dev | 仅手动 | 本仓库直接维护 |

支持 Codex 与 Claude Code，两端共享内容与资源，使用各自真实可用的原生工具。完成后为 7 个 Plugin、23 个 Skills，其中五个第三方分类共 15 项，自有 agent-manager 3 项、personal-dev 5 项。项目级开发工具继续不计入产品。

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

backend-dev 展示增加 FastAPI；personal-dev 展示增加运行诊断。自有 Skill 的 description、Codex display_name / short_description 使用中文。engineering-tools 初始版本 1.0.0；backend-dev 1.1.0；personal-dev 0.6.0。Claude manifest 继续采用既有不写 version 的策略。

## dev-runtime-check

### 触发与授权

仅显式 `$personal-dev:dev-runtime-check` 或 `/personal-dev:dev-runtime-check` 启用，`disable-model-invocation: true`、`allow_implicit_invocation: false`。普通运行故障描述不隐式启动本 Skill。

用户提供 SSH 连接方式并明确诊断目标，就直接连接和执行必要检查，不额外要求一份安全确认或预先列整套审批清单。只有缺少目标地址、认证方式、诊断对象或会影响判断的必要信息时，集中问一个关键问题。可复用当前任务已有授权与已建立连接。

默认执行诊断；用户同时明确要求修复时，完成该目标内的必要修复和受影响验证，不为已授权的普通操作反复确认。单纯诊断不自动扩大为数据清理、重启服务或修改生产配置；具体操作仍遵循当次任务授权和工具真实权限。不得通过 Skill 绕过 Harness 权限、审批或组织控制。

### 轻量执行流程

1. 确定目标主机、服务或容器、症状和时间范围；将本地工作站与远端目标区分。没有 SSH 但已有用户日志时可以分析，远程证据不足如实说明。
2. 使用当前 Harness 可用的 Shell / 终端 / SSH 工具及已有认证。Codex 不套用 Claude 的 Bash / Agent 参数，Claude 不要求 Codex Python helper 或模型选择。默认由当前模型完成，不自动委派，不嵌套启动客户端。
3. 先确认远端主机、操作系统、时间、运行时长及目标进程 / 容器身份。只读取与症状相关的最少证据，按结果逐步深入，不机械收集全部指标。
4. 对 CPU、内存、磁盘 I/O、磁盘空间、网络 / 第三方请求和长期运行问题，区分宿主机 / 容器 / 应用层；速率用两次计数差和实际间隔计算，处理重启和计数回退，单个累计值不推导增长速率。
5. 日志限定服务、时间与行数；采样限定时长与次数；现成工具缺少时使用系统已有证据，不自动安装监控套件、开启持续采集、压测第三方或全盘扫描。
6. 连接和命令使用有限超时，失败说明具体阶段、权限或工具缺失，不无限重试，也不改查本地机器冒充远端证据。允许在授权和当前工具支持下使用必要 sudo。
7. 输出结论、目标 / 时间 / 单位、直接证据、已确认原因与待验证推测、已执行操作和下一步。部署时间相关性不等于因果；区分浏览器到自有后端与后端到第三方请求，应用写入与宿主机实际磁盘写入。

SSH 密码、私钥、token、完整环境变量和连接凭据不写入源码、报告、命令回显或 Git；已有安全认证机制可直接使用。目标命令输出也需按需截取，避免泄露敏感信息。

### 实现规模

新增 `SKILL.md` 与 `agents/openai.yaml` 即可。必要命令示例放在正文，使用明确占位符并说明按远端 OS 选用；不新建 SSH 客户端、连接池、凭据存储、采集器、常驻任务、MCP server 或新依赖。

## 验收

- sources / lock 新增准确两项；旧项与快照不变。证明新分类支持同步、重复同步无差异、上游变化更新、资源与许可证复制，失败可恢复，自有内容不受影响。
- 两端均注册 7 个 Plugin / 23 个 Skills；新第三方项可任务匹配，运行诊断仅手动，并能显式加载正文。完整源文件与安装副本须逐字节一致；若 Harness 限制单次正文注入，记录实测边界，不手改上游快照或将局部注入声称为全文。
- 核对运行诊断场景：给 SSH 和症状直接开始；目标缺失仅补必要问题；累计计数不冒充速率；无法连接不改用工作站；仅诊断不自动变更，明确修复要求可执行；不记录凭据。
- 使用现有 unittest 和隔离客户端 fixture，两个显式开关开启；不改日常客户端配置、不执行真实模型推理。本轮未提供真实 SSH 目标，故不声称远端实机验收。
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
