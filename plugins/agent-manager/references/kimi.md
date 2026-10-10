# Kimi Code 来源与只读检查

仅用于已确认的 Kimi Code Harness，不按模型品牌认领。手动入口为 `/skill:resolve-conflicts`、`/skill:check-updates`、`/skill:configure-project`；Kimi 识别共享 frontmatter 的 `disable-model-invocation: true`，`agents/openai.yaml` 只控制 Codex。

## 来源与加载证据

- 数据根从当前进程的实际 `KIMI_CODE_HOME` / 会话信息确认，缺省为 `~/.kimi-code`。standalone 来源包括该根 `skills/`、真实 OS home 的 `~/.agents/skills/`、当前 Git 项目的 `.kimi-code/skills/` 与 `.agents/skills/`，以及有效 `extra_skill_dirs`。通用用户目录不随 `KIMI_CODE_HOME` 移动。
- 指令来源包括数据根 `AGENTS.md`、通用用户 `.agents/AGENTS.md` / `agents.md`，以及项目根到 cwd 的 `.kimi-code/AGENTS.md`、`AGENTS.md` / `agents.md`。按当前加载器/会话证据核对候选选择、读取顺序、workspace root、额外路径与延迟子目录加载；存在的所有候选不等于同时生效，不照搬 Codex 的覆盖规则。
- 读取已存在的 `<data-root>/plugins/installed.json`：`plugins` 数组中的 `id`、`root`、`source`、`enabled`、`originalSource`、安装/更新时间，以及可选 `github.owner/repo/ref/installedSha`。字段按实际版本核对，损坏或缺失证据标 UNKNOWN。
- 插件根优先读 `kimi.plugin.json`，其次 `.kimi-plugin/plugin.json`。`skills` 明确列一个或多个插件根内 `./` 路径；缺省只认根 `SKILL.md`。Codex / Claude manifest 不能替代 Kimi 清单。
- 本仓库根 `agent-marketplace` 是一次安装 16 个 Skills 的聚合插件；五个分类目录另可本地独立安装。二者不是六份独立能力，同时安装时报告重复来源。以真实路径、Plugin id、Skill 名称和字节证据区分副本；同名项目/用户 Skill 可能覆盖 Plugin Skill，记录当前会话选择。
- 安装复制到数据根 `plugins/managed/<id>/`。receipt 的 enabled、磁盘文件与已安装状态分别记录；修改原目录不改变托管副本，重装后也需要重新加载或新会话。Skill 名称按 Kimi 的大小写不敏感规则比较。

## 更新检查

只读现有 receipt、manifest、明确来源和会话清单；不启动 Kimi、调用 `/plugins` 探测或写配置/缓存。不会读取 credentials、sessions 或完整日志。没有安装证据标 available / UNKNOWN，不按缓存目录推定已加载。

源码根从用户指定 Git checkout 或已记录的来源确认。GitHub 下载得到的托管目录通常没有 `.git`，本地安装的托管副本也不等于仍在维护的源码 checkout。根聚合副本可以读取其 `sources.yaml` / lock 来比较已安装快照；无法定位 Git checkout 时只将 OWNED 的 branch / ancestry 步骤标 BLOCKED，继续有可靠来源的安装与第三方比较。

- `source: github`：使用 receipt 的精确 `installedSha`、原始 URL 和 `github.ref` 还原既定 repo/ref。显式 branch 跟随该分支；显式 SHA/tag 保持固定，不随 main 推进。没有显式 ref 的仓库 URL 按 Kimi 规则取最新 release、无 release 时默认分支，需要只读核验当前目标；无法可靠解析标 UNKNOWN。支持 GitHub API / 已授权连接器读取远端 commit，不运行 Kimi 的安装/更新入口。
- `source: local-path`：`originalSource` 为原始绝对路径，逐文件比较托管副本与该既定目录的 manifest、Skills 及资源。比较结果标 `LOCAL SOURCE`，只说明本地差异；原目录不存在时 UNKNOWN，不从相似目录认领。安装时间/version 相同不足以证明内容一致。
- `source: zip-url`：只有可靠的既有版本/指纹映射才比较。单凭下载 URL、文件名或更新时间不能确认最新版；来源不足标 UNKNOWN SOURCE。不解压/安装远端包做探测。

第三方继续使用共享 `check_sources.py` 按精确 sources/lock identity 比较；有可靠 Git checkout 时 OWNED 按主流程查询其实际 tracking 分支。聚合安装按一个安装对象报告，Skill upstream 各自列行；分类没有独立 GitHub repo URL，不把仓库根安装 receipt 当五个分类 receipt。Kimi 没有本仓库的已注册 Marketplace snapshot 时标 `NOT REGISTERED`，根聚合 Plugin 不冒充 Marketplace 注册。

## 项目开关边界

2026-10-10 核对 Kimi Code Desktop 1.0.4：原生 PluginManager 的开关持久化到用户数据根 `plugins/installed.json`，插件对所有项目生效；官方文档明确尚无项目安装 scope。本版未发现已验证的项目 Plugin / 单个 Skill 开关契约，`.kimi-code/local.toml` 不能凭空增加 enablement 字段。

`configure-project` 对 Kimi 的整个请求返回 `BLOCKED / KIMI PROJECT-LEVEL CONFIGURATION NOT SUPPORTED`，不运行编辑器写入步骤、不改用户开关兜底、不修改或移动 Skill。未来支持需要先补官方契约和真实隔离覆盖证据。

官方依据：[Plugin 安装、manifest 与作用域](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/plugins.md)、[Skill 来源与调用](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/skills.md)、[配置文件](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/config-files.md)。
