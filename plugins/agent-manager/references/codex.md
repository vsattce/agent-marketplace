# Codex adapter

两个 Skill 的业务入口先识别 Harness；此文件仅适用于确认的 Codex。其他 Agent 暂不支持。

Codex Plugin 手动调用使用 `$agent-manager:resolve-conflicts`、`$agent-manager:check-updates`；本机 0.162.0-alpha.2 的裸 `$resolve-conflicts` / `$check-updates` 未注入 Plugin Skill 正文。不得以复制用户 standalone Skill 或配置永久 alias 来补别名。

## 每次执行先核验官方机制

联网读取这些官方页面的当前内容，不只看搜索摘要。链接迁移则沿官方重定向查找；不能访问或无法确定机制时，修改步骤 BLOCKED，只读步骤保留已证实结果与 UNKNOWN 原因。

- [Plugin 结构、项目 enable/disable 与 Marketplace](https://developers.openai.com/plugins/build/plugins)
- [Skill 元数据、调用策略与禁用](https://learn.chatgpt.com/docs/build-skills)
- [配置路径、信任与优先级](https://learn.chatgpt.com/docs/config-file/config-basic)
- [配置字段](https://learn.chatgpt.com/docs/config-file/config-reference)
- [App-server 官方接口](https://learn.chatgpt.com/docs/app-server)

2026-10-10 已核验基线，**不是无需复核的永久字段**：用户配置通常在 `$CODEX_HOME/config.toml`（未设置时 `~/.codex/config.toml`），受信任项目使用 `.codex/config.toml`。CLI overrides > 项目根到 cwd 的配置（最近优先）> selected profile > user > cloud defaults > system > built-ins，另受 enforced requirements 限制。只写当前项目根配置；有子目录 override、CLI/profile 强制值或 managed 控制时先证明目标层会生效，不能修改高层绕过。

当前项目 Plugin 控制示例：

```toml
[plugins."example@marketplace"]
enabled = false
```

此机制针对支持的本地 Marketplace Plugin；workspace-managed Plugin 不承诺可用此字段控制。不要将 universal connector/app ID 当成本地 Plugin key。

官方存在 `[[skills.config]]`、`path`、`enabled`。Build skills 示例给 SKILL.md 路径，configuration reference 描述为 Skill 目录；当前安装版本的 loader 才能确定实际接受哪个路径。对 standalone 或 Plugin Skill 控制必须使用官方有效 skills/list 返回路径并验证。按 name 不足以区分同名来源，禁止生成 name selector。

2026-10-10，本机 `codex-cli 0.162.0-alpha.2` 隔离测试：项目层 rules 在 `config/read` 可见，但 `skills/list` 的 global Plugin 目标仍 enabled；精确 SKILL.md 和目录 selector 均无效。临时用户层相同 SKILL.md rule 有效。项目 handoff 和全局 research / diagnosing-bugs 等保持启用。此版本对用户要求的持久化项目隔离为 BLOCKED；每次执行仍重新探测，不把历史结果当永久限制。不得改全局配置或以 Plugin disable 代替。

## 本地只读证据

resolve-conflicts 的「项目外绝不写入」边界同时约束本 adapter。先从当前 Harness 元数据获取版本；只有确认进程本身及其子进程无项目外写入才运行 CLI（包括 --version / --help / list）或新 app-server。只设置 CODEX_HOME 不构成约束，接口名 read/list 也不证明日志、缓存和状态文件只读。可使用已有会话中已证实只读的接口或读取已存在的 metadata；证据不足就 BLOCKED，绝不通过修改 trust、全局配置/缓存或安装测试 Plugin 继续。

当前基线支持以下查询入口，但执行仍受上述边界限制：

```text
codex plugin list --json
codex plugin list --available --json
codex plugin marketplace list --json
```

只有确认本版本 list 无安装/刷新副作用才执行；否则读取现有 metadata。禁止把 add / marketplace upgrade 当作状态查询。list 的版本和 enabled 字段不是实际注入的全部证据。

需要 loader/config 精确证据时，核对官方 app-server 文档及现有本机 protocol schema，在满足执行边界后才使用 `skills/list`、`config/read`（需要时 includeLayers）；不要猜请求格式。不能取得时报告证据不足。不要输出完整 config/read，可能含密钥。之前在系统临时目录安装测试 Plugin 和修改临时用户配置的探测已撤出 Skill；`probe_codex.py` 只读文件并 BLOCKED，不是实际过滤验证。历史 0.162.0-alpha.2 测试结论保留作背景，每次仍需当前证据。

识别项目 trust：核对有效配置层来源与用户配置的 projects/trust metadata；只有实际加载项目层才可写。新建项目配置尚未存在时，用已验证的本机 trust metadata确认该项目层可以加载。不得自动修改用户 trust。同一 Plugin 在项目 catalog 出现且全局安装，不足以证明是项目来源；结合加载路径、安装来源、配置层和 project catalog 判断。

从官方返回路径读取 manifest 和实际 SKILL.md 的 frontmatter，记录 name、namespace、description、Plugin identity、来源层级、enabled 状态。未启用或只有缓存文件的项目不算有效重复。MCP/hooks/apps 与自定义加载目录也属于 Plugin 连带能力。来源格式无法安全识别时停止该冲突处理。

## 增量修改与验证

使用 resolve-conflicts 的 helper `edit_config(project, plugin_updates=..., skill_updates=...)`，参数只包含扫描后确定的目标。`write_path(project, target)` 将 project 与**调用时 cwd 识别的根目录**比较；传入另一个 Git 项目也被拒绝。每次创建、写入、替换、chmod、临时文件和失败清理均重新检查 canonical 包含关系、用户目录禁区及 symlink/junction/hardlink。它只编辑项目 `.codex/config.toml`，保留 TOML 注释/格式；未支持结构、重定向、权限不足或并发修改 BLOCKED。Skill path 参数可引用项目外文件，但只是读取/selector，不是写目标。

helper 需要已有 Python 3.12+、tomlkit 0.13.x、PyYAML 6.x；先服从目标项目约束核对 mise，不匹配 BLOCKED。以 `python -B` 执行，不在全局 Plugin 源码产生 bytecode；不能为此写入项目外的 uv 环境、依赖缓存或全局包目录。所需依赖不可安全取得则停止执行。路径检查不能约束任意外部进程，不能把 helper 说成系统级 sandbox。

编辑前再次核对有效状态；完成后重新读 TOML，重新做官方 loader 发现并对比相关 Skills，核对用户 config 字节未变。需要新会话/重启才能加载时报告 `PENDING RELOAD` 和 Unresolved，不声称即刻生效。不能验证时不扩大修改。

## 更新证据

将 installed Plugin receipt/cache 的精确版本与其原先 Marketplace source 对比。GitHub repo/ref 来源用 ls-remote 或 GitHub API 查同一目标，记录 snapshot commit；npm 只查已记录 registry/package/version 目标；local 来源只比较实际 catalog/文件指纹，并标注 LOCAL SOURCE。无法映射安装 commit 时 UNKNOWN，禁止猜 cache 版本目录等于远端最新。

standalone upstream 仅来自已有 receipt、明确配置或所属 Git repo。owned commit ancestry 只基于当前 tracking branch 的精确远端 SHA；已有 origin/<branch> 可能陈旧，不把它当实时远端。
