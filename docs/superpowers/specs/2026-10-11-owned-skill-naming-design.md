# 自有 Skill 命名调整 Spec

## 授权与目标

用户已确认只做自有 Skill 命名的微创调整，并明确授权先生成 spec / plan，再通过当前已安装的 `personal-dev:delegated-development` 执行、验证、提交并推送当前分支。该旧入口仅记录本轮执行来源，不作为调整后的调用示例。

目标是在客户端的 Skill 选择器中更容易按 `dev` / `am` 搜索个人开发和 Agent 管理能力。插件身份不变，不创建 Router、别名 Skill、二级菜单、统一 namespace 或其他架构。

| 插件 | 原 Skill 名 | 目标 Skill 名 |
| --- | --- | --- |
| personal-dev | delegated-development | dev-delegate |
| personal-dev | review | dev-review |
| agent-manager | check-updates | am-update |
| agent-manager | configure-project | am-config |
| agent-manager | resolve-conflicts | am-conflict |

## 命名与行为边界

- 自有 personal-dev Skill 后续采用 `dev-{action}`，agent-manager 采用 `am-{action}`；保持简短、动作导向。此命名规则记录在现有维护文档，不新增治理设施。
- 插件名、插件身份、发现根目录及安装分类保持不变。frontend-dev、backend-dev、common-workflow、testing-automation 和第三方快照均保持原样，sources.yaml / sources.lock.json 不修改。
- 不改变正文的业务规则、触发策略、权限边界、流程和功能。仅手动调用的 frontmatter / agents/openai.yaml 策略继续保留。
- am-update 仍只读检查更新，am-conflict 仍只读查找和报告，am-config 的项目写入及 BLOCKED 边界保持不变。
- personal-dev 保持仅 Codex / Claude Code 支持，不加入 Kimi。agent-manager 同步已有三端调用与加载契约。
- Codex 完整调用为 `$personal-dev:dev-delegate`、`$personal-dev:dev-review`、`$agent-manager:am-update`、`$agent-manager:am-config`、`$agent-manager:am-conflict`；Claude 使用同名 `/plugin:skill`，Kimi 管理入口使用 `/skill:am-*`。
- `$dev` / `/dev`、`$am` / `/am` 是筛选目标，不是新增调用别名。原生发现/正文注入与输入框搜索是不同验收层次，不能用加载测试代替 UI 搜索实测。现有隔离 fixture 无法证明的 UI 行为需如实列为未验证，不修改日常全局配置来补证。
- 旧完整调用名会失效，不保留重复入口。仓库提交不等于用户已安装副本更新；文档说明刷新 / 新会话要求，不自动修改用户缓存或全局安装。

## 同步范围

重命名五个 Skill 目录及各 SKILL.md 的 name；同步自有正文中的显式调用、default_prompt、manifest / marketplace 中实际受影响的介绍、配置、脚本路径、兄弟资源引用、现行文档及测试。无旧名引用的 manifest 不为凑齐清单而修改。

dev-review 的 scripts/select_models.py 直接引用兄弟 dev-delegate/scripts/select_models.py，该引用必须可加载，算法及输入输出不变。测试文件名 / 函数名是内部职责名称，无须为命名规则机械改为 CLI 名；失效路径及期望值必须更新。

相关插件版本根据现行安装标识策略作最小必要递增，Codex manifest / catalog metadata 必须一致；Claude manifest 无 version 的既有策略继续保持。

## 旧名残留语义处理

全仓库搜索包含隐藏的产品入口及配置，排除 .git、忽略的临时目录和安装依赖。检查 delegated-development、personal-dev:review、check-updates、configure-project、resolve-conflicts，以及自有 `skills/review`、`name: review`、测试中对应目录/名称常量。

- 现行入口、调用、链接、资源路径和测试契约不得保留旧名。
- `configure_project.py` 的 `.configure-project.lock` 保留，确保新旧版本共享并发锁。对应测试与必要兼容注释为允许残留；不改锁行为。
- 历史 docs/superpowers/specs、plans、reviews 可保留当时名称、版本和已执行命令；历史文件内仍需可点击的链接改成新路径。记录历史不应机械改写为新版本已经验收。
- 本次 spec / plan 的迁移表、扫描命令和执行来源可以使用旧名。
- 普通 review 角色、变量、原生 /review 和其他上下游术语不是本次 Skill 标识，不做全局替换。
- 每个保留命中都有明确语义，最终验证记录列出残留类别。临时文件前缀可同步到 `.am-config-`，永久锁名必须保留。

## 验收与交付

1. 五个目标目录存在，frontmatter name 与目录一致；旧目录不存在；插件身份、Skill 数量、手动策略及随包资源保持一致。
2. 现有模型选择与配置事务测试继续通过，特别是兄弟脚本导入、失败/回滚和旧锁保护。
3. 运行现有完整 unittest，必要的 Codex / Claude manifest 校验及隔离原生加载测试；Kimi 使用既有 ASAR fixture 验证管理工具新名称、安装与资源发现。仅用已有 opt-in 开关，不改全局环境。
4. 核对旧名残留、现行本地文档链接、git diff --check、第三方文件零改动。无法执行的验证说明具体边界，不以 skipped 宣称实测通过。
5. 独立验收覆盖 staged / unstaged / 新文件；主模型终审后仅暂存任务文件，以中文 Conventional Commit 提交并非强制推送当前 main，核对远端 SHA 和工作区。

### 实测后确认的两项测试环境适配

首轮启用两端隔离加载的全量测试运行 133 项，129 项通过，4 项仅因 Claude 测试把当前 2.1.296 与单值 2.1.291 比较而失败；产品既有已验证版本集合已包含两个版本。允许测试断言使用该已有集合，不增补产品版本白名单或修改配置能力。

Windows 逃逸测试原本固定访问 Z:/outside/config.toml，本机 Z: 为网络盘，路径解析出现异常等待。允许仅把测试 fixture 改成从 os.listdrives() 选择未挂载盘符，保持原跨盘逃逸断言，避免访问网络盘；产品 safe_path 不修改。这两项改动仅使现有验证在当前环境可执行，不属于 Skill 功能变更。

## 执行基线与委派

- 目录：E:/WorkSpace/agent-marketplace，分支 main，基线 29c3b386d26d48ca7c3311ea18467a10c97efb4f；初始 tracked / staged / untracked 均干净。
- 当前干净 checkout 上原地执行，保留当前分支；不新增隔离 checkout 或分支。
- 用户明确指定 6luna，当前 spawn_agent 允许 gpt-6-luna；helper 通过精确覆写返回 READY。主模型型号不从历史配置猜测。
- 编码 gpt-6-luna / xhigh；另一干净上下文代理验收 gpt-6-luna / max。禁止子代理派生、commit / push 或全局修改，初次实现后最多两轮修复与独立复验。
- 已核验 mise Python 3.12.13 / Node 24.19.0，Python 满足仓库 3.12+；uv 0.12.3。命令使用 mise 解释器与 uv，不安装/切换运行时。
