# DeepSeek Harness 桌面版项目编辑与冲突检查

供用户明确调用 `/am-config` 时使用，当前按 dsh 桌面版 `0.2.1-rc.2` 的 Skill 机制核验。默认只写当前项目；日常 `~/.dsh`、桌面 profile、其他客户端和全局来源只读，不运行 Codex / Claude 的配置编辑器，不提交或推送。

## 检查与项目编辑

先确认当前 Harness、workspace / Git 根、目标项目规则及用户指定范围。用户只要求检查时，按[冲突分级](../skills/am-config/references/conflicts.md)读取必要文件并在聊天中报告，缺少实际加载证据时标 `PARTIAL / UNKNOWN`；不启动模型探测、建立 profile 或修改全局来源。

沿用[项目文件预检](../skills/am-config/references/project-edits.md)的来源、目标、冲突、写前复核与恢复要求，应用以下 dsh 分支：

- **项目指令**：可按明确要求原位编辑项目 `AGENTS.md`。仅凭 Skill provider 的项目根算法不能推断指令加载链；按目标会话实际注入核实，未证实时报告 `LOADING UNKNOWN`，不自动复制其他客户端规则或补引用。
- **standalone Skill**：从用户明确指定的来源保留完整必要资源，复制到项目 `.dsh/skills/<name>/`；已有 `.agents/skills/` 也会被 dsh 扫描，先检查同名和重复。dsh 只发现根目录直接的 `<name>/SKILL.md` 或 `<name>.md`，不递归发现嵌套插件；带插件共享引用的 Skill 应保留完整包并另行确认加载根，不能只抽走一个目录。
- **产品文件准备**：可按明确请求在项目内准备完整插件目录、资源和许可证。原有 Codex / Claude manifest 不证明 dsh 已安装或已加载，准备状态单独报告。
- **项目 Plugin 开关 / 原生扩展安装**：本次未验证 dsh 的仅项目作用域，报告 `BLOCKED / PROJECT PLUGIN SCOPE UNVERIFIED`；不以修改用户 desktop profile、调用 npm 或全局插件管理替代。

## 来源、优先级与调用

dsh 默认 Skill 根为项目 `.dsh/skills`、项目 `.agents/skills`、额外 `customSkillDirs`、用户 `~/.dsh/skills`、用户 `~/.agents/skills`，同层按此优先级选择；项目根为最近 `.git` 祖先，无标记时为 cwd。用户根及额外根以实际配置为准，不能从 npm CLI 推断桌面 profile。

`/am-config` 由用户直接输入；保留 `disable-model-invocation: true`。`agents/openai.yaml` 仅供 Codex。分别报告文件已准备、配置是否保存、隔离加载是否通过及当前会话是否实际注入，不把磁盘存在当作生效。

依据：[桌面版](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/apps/desktop/README.md)、[文件系统 Skills](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/packages/skill/skill-filesystem/README.md)。
