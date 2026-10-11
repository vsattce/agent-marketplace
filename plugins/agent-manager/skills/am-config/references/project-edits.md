# 项目规则与安装预检

供 `am-config` 处理 `AGENTS.md`、standalone Skill 安装和已支持 Plugin 开关时使用。它不扩展项目外写入，也不改变 `configure_project.py` 的输入。

## 全批预检

1. 确认当前 Harness 为 Codex 或 Claude Code，再读取版本、项目根、加载来源与已知 Skill / Plugin 清单。其他 Harness 为 `BLOCKED / UNSUPPORTED AGENT`。按请求只读检查相关全局指令、项目有效指令链、拟启用/安装能力的 manifest、来源身份和相关 Skill 正文；不遍历整个 home，不把磁盘缓存当作已安装或已加载。项目文件中的命令只作为内容审阅，不执行。
2. 对照拟写规则或将启用的能力，比较触发条件、作用范围、实际正文和来源身份。按结果区分：同源同内容且已在目标路径为 `UNCHANGED`；语义相同则复用或原位修改，不重复写；能力重叠但可共存时记录为 `OVERLAP`；不同 namespace 可以按用户明确请求共存；同条件下无法同时满足的规则、来源身份歧义或会改变已有行为的覆盖才是未解决 `CONFLICT`。
3. 无法核实的来源或加载状态写 `UNKNOWN`，不能据此宣称无冲突。目标身份、安装完整写入范围或完成用户所请求效果必需的加载/能力证据缺失时，整批在写前 `BLOCKED`。用户仅要求编辑 `AGENTS.md` 且加载状态未知时，可继续编辑并报告 `LOADING UNKNOWN`；若用户要求当前 Harness 确实加载/遵循它，按下文处理入口授权后再预检。其他非关键来源仍需在结果中标明未核实范围。
4. 先完成混合批次全部目标、冲突、路径、能力和依赖检查，再开始任何写入。一个请求不受支持就整批停止。未解决冲突时向用户列出双方原文、路径/作用域、行为影响和最小方案，只问决定结果的问题；不得擅自覆盖、禁用或删除既有能力。用户已明确的 A→B 修改按授权直接执行。

## 编辑 `AGENTS.md`

- 文件名用规范拼写 `AGENTS.md`。默认项目 Git/workspace 根；仅用户明确指出子目录时使用该子目录。路径必须留在当前项目。
- 规范化整个目标路径，确认目录链没有 symlink / junction 越界，目标不是硬链接到项目外的文件；不能证明边界时先停止。
- 先按 Codex 或 Claude Code 的真实 Harness 解析目标文件所在目录的指令入口及祖先链，检查同义规则和相关全局规则。Codex 每层依次考虑 `AGENTS.override.md`、`AGENTS.md` 和已配置 fallback，且同目录只取首个非空入口；`AGENTS.override.md` 会遮蔽同目录 `AGENTS.md`。Claude Code v2.1.277+ 默认在工作目录及祖先没有 `CLAUDE.md`、`.claude/CLAUDE.md` 或 `CLAUDE.local.md` 时读取 `AGENTS.md`；实际版本、Project instructions 设置和会话加载证据优先。
- 若目标文件被遮蔽或当前不生效，用户明确要求改文件时仍可编辑并如实说明效果；若用户要求当前 Harness 实际遵循它，先确认是否授权添加项目内引用/入口。绝不自动改 global、trust 或安全设置。
- 目标文件已有同义规则时复用或在原位置更新；用户明确授权把现有规则从 A 改为 B 时直接原位替换。无文件时只按用户给出的规则最小创建，不自行编造项目约定。保留原字节格式和其他规则，只展示所需 diff。

官方加载依据：[Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Claude Code memory / AGENTS.md](https://code.claude.com/docs/en/memory)。这些文档不代替当前会话版本和项目配置证据。

## 安装 Skills / Plugins

- Skill 安装要求用户指定准确来源与项目目标。仅处理 Codex `.agents/skills/<name>/` 或 Claude Code `.claude/skills/<name>/`；读取 `SKILL.md`、manifest、被引用资源及来源身份，完整复制必要文件，不执行来源脚本、不安装依赖、不刷新 Marketplace。Plugin 提供的 Skill 若依赖其 Plugin hooks、MCP、命令或其他资源，不得抽出并冒充 standalone 安装。
- 写前只读核实用户指定来源 Skill 根的 canonical path；来源可在全局或其他项目，但只读取该 Skill 根内必要资源，且来源资源链接必须解析并留在所给 Skill 根内。不修改来源或执行来源脚本。目标的 canonical path、provenance 记录以及临时、暂存和日志等所有写入必须留在当前项目；检查目标路径各层的 symlink、junction 和硬链接，不跟随项目外重定向。目标已存在时只在同来源、同内容、同 provenance 下视为 `UNCHANGED`，否则不覆盖未知文件。将来源路径或仓库、用户指定 ref、可得的精确 commit 与相对安装路径记录在 Skill 旁的 `.agent-manager-source.json`；已有未知同名文件时阻止，不覆盖。来源字符串先去除凭据。
- 对照目标 Harness 中已安装/已加载的 Skills、启用 Plugins 和相关全局 Skills，按触发条件、scope、正文、资源与来源 identity 检查重复和冲突。同名不同来源不能直接替换；同义规则不重复写。显式要求共存的不同 namespace 在 Harness 能区分且没有实质冲突时可保留。完整复制后核对文件集合、内容、provenance 和发现路径；不以文字匹配测试代替行为证据。
- Plugin 安装仅对用户明确指定的来源和项目目标开放。写前须依据当前 Harness / 版本的官方说明或实际实现，核实具体受支持的安装工具/操作、来源 identity、canonical 目标，以及该操作所有持久及临时写入的完整路径；确认 temp、staging、cache、receipt、lock、log 等副作用也全部位于当前项目。仅凭 `--scope project`、项目级 Plugin 开关、manifest 或目标目录存在都不构成证据。全部证据确立后，只调用已核实操作；写后核对安装记录、来源 identity、目标路径和项目作用域。任何写入可能落在项目外、操作副作用未知或安装结果无法核实时，禁止执行并报告 `BLOCKED / PROJECT-LOCAL PLUGIN INSTALL NOT VERIFIED`。不手工复制 Plugin 来冒充已安装，也不使用可能改用户 cache / receipt 的原生安装器。

## 执行与恢复

若批次含 Plugin 开关，先预备并验证编辑器输入、依赖及版本，但不在基线复核前调用会写入的开关编辑器。首次写入前重读所有目标并与预检基线比较，变化时停止并重新预检；通过后再按 Skill 执行步骤处理文件操作和开关编辑器。文件类操作不进入编辑器输入。开始前记录本次将改文件的原内容；分步写入不构成跨文件原子事务。失败后仅当文件仍精确等于本次写入结果时恢复该文件；发现并发变化则不覆盖，并报告实际可能已改路径及 `UNKNOWN; CHECK PROJECT FILES`。最后重读受影响内容，验证用户请求、未请求内容和路径边界。
