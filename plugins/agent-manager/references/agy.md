# Antigravity CLI（agy）项目编辑与冲突检查

供用户明确调用 `/am-config` 时使用。默认只写当前项目，相关全局来源始终只读；不调用 Codex / Claude 的 `configure_project.py`，不修改日常用户设置、信任、权限、模型或 MCP，不提交 / 推送。

## 来源与只读检查

按当前 workspace / Git 根确认项目及本轮 Harness，按请求读取当前会话可用清单和必要文件。项目规则包括适用路径上的 `AGENTS.md`、`GEMINI.md`、`.agents/AGENTS.md`、`.agents/GEMINI.md` 与 `.agents/rules/*.md`；相关全局规则只读检查 `~/.gemini/` 与 `~/.gemini/config/` 下的规则入口。不同路径的规则可能累计加载，不能套用 Codex 的同层首文件遮蔽机制。

项目 Skills 使用 `.agents/skills/`。全局 Skills / Plugins 的路径以本机版本、实际清单与 receipt 为准；可用原生命令为 `agy plugin list --json`，不把源码、安装文件或启用状态直接当作当前对话已加载。`agents/openai.yaml` 只控制 Codex；agy 的手动入口仍需遵守正文明确调用条件。

用户只要求检查时，按[冲突分级](../skills/am-config/references/conflicts.md)只读检查并在聊天中报告，来源不可读或实际加载未证实则标明 `PARTIAL / UNKNOWN`，不建立探测会话或修改安装状态。

## 项目编辑

沿用[项目文件预检](../skills/am-config/references/project-edits.md)的来源、路径、重复 / 冲突、写前复核与恢复规则，并应用以下 agy 分支：

- **项目指令**：按用户要求原位编辑 `AGENTS.md`，结合当前有效规则链检查冲突；不自动添加另一份指令副本。文件已保存与当前会话是否加载分别报告。
- **standalone Skill**：从用户指定来源完整复制必要资源到项目 `.agents/skills/<name>/`，保留许可证与来源记录；不抽取依赖 Plugin hooks / MCP 的 Skill 冒充独立安装。
- **项目 Plugin 准备**：可在项目内准备完整插件目录和 agy 能识别的 `plugin.json` 或 `.antigravity-plugin/plugin.json`；使用 `agy plugin validate <path> --json` 检查。准备成功不是已安装 / 已加载。
- **Plugin 项目开关 / 项目安装**：当前已验证的 `agy plugin install / enable / disable` 会操作用户级插件，不用于“仅当前项目”的要求。没有当前版本明确的项目作用域证据时，报告 `BLOCKED / PROJECT PLUGIN SCOPE UNVERIFIED`，保留已完成的文件准备，不转向全局操作或伪造项目配置。

批次写入前先查完全部目标；未决实质冲突先停止相关批次。仅编辑明确授权的文件，写后分别报告文件准备、校验与实际加载，当前会话加载未经证实则写 `LOADING UNKNOWN`。不运行来源脚本或真实模型探测来验证加载。

依据：[agy 规则](https://antigravity.google/docs/rules/)、[Skills](https://antigravity.google/docs/skills/)、[Plugins](https://antigravity.google/docs/plugins/)。
