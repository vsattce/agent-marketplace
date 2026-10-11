# personal-dev 开发约束与精简 Skill 实现计划

> **For agentic workers:** 用户已显式选择 `dev-delegate` 并授权 spec / plan 后直接执行，覆盖通用计划等待确认及执行方式建议。主模型编写文档；一个 `gpt-6-luna` / `xhigh` 编码代理完成关联实现，另一个干净上下文的 `gpt-6-luna` / `max` 独立验收。子代理不继续派生、不 commit / push；主模型亲自验证双端并提交推送。

**Goal:** 为 personal-dev 增加手动调用的 dev-yagni / dev-simplify，分别提供当前任务的最小实现约束和行为等价精简。

**Architecture:** 两个自有共享 Skill 正文，沿用 frontmatter 与 agents/openai.yaml 双端调用策略；显式委派复用既有交接契约。无新增运行时代码、依赖或自动流程。

**Tech Stack:** Markdown、YAML、JSON；Python 3.12+ / uv / unittest；原生 Codex / Claude 隔离加载 fixture。

**Spec:** `docs/superpowers/specs/2026-10-11-personal-dev-quality-design.md`

## Global Constraints

- 仅 Codex / Claude Code，所有新入口仅用户显式手动调用；不互相调用、不自动串联、不默认派代理。
- dev-yagni 默认执行，明确先看方案才等待；dev-simplify 默认建议，明确执行或确认后才编辑。
- 当前项目 / 当前任务 / 明确范围，保留已有改动与全部必要行为边界，无全局配置写入和隐含权限。
- Codex personal-dev `0.5.0`；六个 Plugin、20 个 Skills；Claude manifest 不新增 version。
- 保留第三方 sources / lock 和原有 dev-delegate / dev-review 行为，不新增运行时依赖、脚本、报告模板、别名机制。
- 原主检出 E:\WorkSpace\agent-marketplace 的 `docs/reviews/` 是已有未跟踪内容，不加入此次提交。

## Review Focus

- 含调用名的引用或“先看看方案，暂时不要执行”：判断完整语义，不误写。
- 默认执行且没有开发目标 / 默认精简却没有 diff：询问目标或范围，不发明任务。
- 用户混杂改动与已提交代码：不能覆盖已有内容或自动改全项目。
- 简化影响错误、日志、调用顺序、事务、并发或资源释放：保留行为，不能为减行数削弱保障。
- 显式委派与建议模式同时出现：交接约束且保留等待确认；不要假设双端同一条消息的命令解析一致。

## Task 1: 手动 Skill 与包装文档（同一编码代理）

**Create:**
- `plugins/personal-dev/skills/dev-yagni/SKILL.md`
- `plugins/personal-dev/skills/dev-yagni/agents/openai.yaml`
- `plugins/personal-dev/skills/dev-simplify/SKILL.md`
- `plugins/personal-dev/skills/dev-simplify/agents/openai.yaml`

**Modify:** `plugins/personal-dev/plugin.json`、`plugins/personal-dev/.claude-plugin/plugin.json`、`.agents/plugins/marketplace.json`、README.md、docs/usage.md、docs/maintenance.md、tests/test_personal_dev_packaging.py、tests/test_personal_dev_loader.py、tests/test_claude_loader.py。仅直接需要时调整其他既有数量断言。

**Interfaces:** 原生 namespaced 调用名及手动加载策略；用户显式 dev-delegate 通过现有 roles.md 交接，无新 helper 接口。

- [x] **1. RED。** 先更新 packaging 对四个目录、0.5.0、两个新 Skill frontmatter / YAML、无额外脚本和来源边界的断言；运行 `uv run --python (mise which python) --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -p test_personal_dev_packaging.py -v`，观察新入口不存在的失败。保存实际摘要，不把已通过断言当行为验收。
- [x] **2. GREEN。** 按 spec 独立撰写简短正文与 metadata，建议 / 执行默认值写进 UI default_prompt；不额外读取外部资料或自动安装工具。依次自查两个 Skill 的实际条件分支与范围。
- [x] **3. 包装与说明。** 同步 manifest / Codex catalog interface、Claude 描述、README 数量和入口、usage 默认行为及显式委派示例、maintenance 测试说明。旧 Skill 正文及工具策略不改。
- [x] **4. 加载契约。** 扩展 Codex / Claude 既有隔离测试：四入口发现、普通相关请求不注入新正文、两个显式调用分别注入；Codex 验证同消息显式组合，Claude 按实际 native parser 记录组合边界，不造新基础设施。fixture 不执行真实推理。
- [x] **5. 自检。** 在工作树核对 mise / Python，仅进程设置 PYTHONUTF8=1、PYTHONIOENCODING=utf-8、TMP/TEMP 为规范工作树目录，运行相关 personal-dev 测试与 git diff --check；回传文件列表、RED/GREEN 结果、必要验证、限制与疑点，不 commit。

## Task 2: 独立验收与主模型双端验证

- [x] **1. 独立验收。** 新的 gpt-6-luna / max 代理读 spec / plan / 实际累计 diff，检查需求、质量、范围与证据；用简短场景回答实际应采取的动作，覆盖 Review Focus 和两种默认行为。允许无精简候选，禁止为凑修改去改。记录 PASS / FAIL / UNVERIFIED 及有证据的阻塞，最多两轮定向修复复验。
- [x] **2. 主模型验证。** 核实独立报告和实际实现；亲自开启 AGENT_MANAGER_CODEX_TESTS=1 / AGENT_MANAGER_CLAUDE_TESTS=1 的原有隔离 fixture，至少跑新 personal-dev Codex 加载和 Claude personal-dev / discovery 加载。按需求补充剩余相关回归或全套。原生工具版本以本轮实测为准。
- [x] **3. 最终证据。** 记录本轮实测版本、命令、通过 / 跳过数、场景和组合限制到现有 maintenance 文档的本次记录；更新本计划进度。无真实业务模型推理，不声称桌面 UI 或生产项目端到端通过。
- [x] **4. 本地交付检查。** 主模型核对所有 tracked / staged / 新文件、第三方无差异及 git diff --check；在确认原 main 未被改动后安全应用任务差异及新增文件到主检出，运行完整回归。保留 docs/reviews/。

**Git 收尾：** 验证通过后仅提交任务文件，非强制推送 origin/main 并核验远端哈希；归档本任务原生工作树。计划随实现提交，实际提交、推送与归档结果在对话收尾汇报，不以计划勾选代替远端状态证据。

## 执行记录

- 起始基线：36 个 personal-dev 测试，35 通过、1 个原生 opt-in 跳过。最初只设 PYTHONIOENCODING 导致子进程 UTF-8 输出与父进程 GBK 解码不一致；仅本次测试进程同时设 PYTHONUTF8 后基线通过，无源码或全局配置修改。
- 实测工具：Python 3.12.13、uv 0.12.3、Codex CLI 0.162.0-alpha.17.2、Claude Code 2.1.296。
- 编码 / 验收策略：用户明确指定 gpt-6-luna；helper READY，编码 xhigh、验收 max。主模型精确型号 UNKNOWN，使用已确认的精确 model_override，不推测型号。
- 修复轮次：1 / 2。初次验收指出默认 diff、执行授权、委派交接、任务生命周期、Git 权限措辞、依赖选择、旧数量断言及 Claude 组合调用说明的问题；原编码代理集中修复后，独立代理定向复验需求 PASS。
- 无新增 Skill 指导的六个独立场景动作判断：控制组 C 对“帮我精简当前 diff”选择直接编辑；E 在无 diff 时选择先猜测最近提交范围。新 Skill 需要分别改为默认建议及先明确范围；A/B/D/F 的正常判断保留。该控制组只回答下一步，没有实际写入或原生客户端推理。
- 主模型首次双端全量回归：147 个用例，1 个旧数量断言失败（20 != 18），3 个项目配置错误。新 Skill 的双端发现、手动注入及普通提示不注入检查通过。配置错误是既有 protected_roots 规则拒绝 .codex 下的原生工作树位置，保留保护规则；最终完整回归改在原 E: 主检出执行。
- 组合语法实测：Codex 同消息两个显式入口都注入；Claude 同消息只直接注入首个入口（dev-yagni=True / dev-simplify=False）。文档需推荐先后显式调用，并区别原生加载与实际工作流判断。
- 最终主检出回归：在 E:\WorkSpace\agent-marketplace 开启两端原生隔离测试，运行完整 unittest，147 项 / 45.695 秒 / OK，退出码 0，无跳过。测试命令与上方计划一致，仅本次进程设置 UTF-8、TMP / TEMP 与两端 opt-in；临时 fixture 存放在已有 `.skill-sync-*/` 忽略范围，未改日常全局配置。
- 最终独立证据核验：验收代理读取完整输出，并核验主检出与工作树的 11 个 Skill / metadata / 测试文件 SHA-256 一致；需求 PASS、质量 PASS。没有重复运行 suite，也未宣称真实模型或桌面 UI 全流程通过。
- 交付基线：原 main 保持 d9b95c9e13b44aa586fca8faa1dc02cc65b7d163；任务 tracked patch 先通过 git apply --check，再应用并逐项复制六个新文件。原有 docs/reviews/ 保留，工作树内测试探针不复制、不提交。
