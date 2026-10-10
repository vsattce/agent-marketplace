# agent-marketplace

个人使用的 Codex Plugin / Skill 市场，显示名称为 **Agent Marketplace**。Marketplace 整理可选来源，项目实际启用哪些插件由 Codex 配置控制。

按 upstream / Skill Bundle 分组，每个包只加载选定的 Skills。当前有八个包，共 13 个 Skills，第三方能力通过 Marketplace / Plugin 安装管理。

## 当前结构

```text
agent-marketplace/
├── .agents/plugins/marketplace.json
├── AGENTS.md
├── README.md
└── LICENSE
```

本仓库只保存 Marketplace 指针和 metadata，**没有第三方 SKILL.md、scripts、references 或 assets 副本**。第三方内容由 Codex 从 upstream 下载到安装缓存。

## 插件与来源

入口使用 Codex 原生远程来源。多数包使用 `git-subdir`，Plugin 根为 upstream 的 `skills/`；Currents 包使用 `url` 指向仓库根。`skills` 数组相对于 Plugin 根，只加载列出的目录。

| Plugin 标识 | 展示名称 | 安装来源 | 加载的 Skills | License |
| --- | --- | --- | --- | --- |
| `matt-skills@agent-marketplace` | Matt 工作流 | [mattpocock/skills](https://github.com/mattpocock/skills)，`main` | handoff、diagnosing-bugs、research、writing-for-agents | [MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| `anthropic-skills@agent-marketplace` | Anthropic 前端与测试 | [anthropics/skills](https://github.com/anthropics/skills)，锁定 commit | frontend-design、webapp-testing | Apache-2.0，见各 Skill 的许可证 |
| `vue-skills@agent-marketplace` | Vue 开发技能 | [antfu/skills](https://github.com/antfu/skills)，锁定历史合集 commit | vue、vue-best-practices | MIT，见合集及各 Skill 的许可证 |
| `vercel-skills@agent-marketplace` | Vercel Skills | [vercel-labs/skills](https://github.com/vercel-labs/skills)，`main` | find-skills | [MIT](https://github.com/vercel-labs/skills/blob/main/LICENSE) |
| `web-design-guidelines@agent-marketplace` | Web 设计规范 | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)，`main` | web-design-guidelines | 当前 upstream 未提供仓库 LICENSE，不标注为 MIT |
| `java-spring-boot@agent-marketplace` | Java / Spring Boot | [pluginagentmarketplace/custom-plugin-java](https://github.com/pluginagentmarketplace/custom-plugin-java)，`main` | java-spring-boot | [上游自定义许可证](https://github.com/pluginagentmarketplace/custom-plugin-java/blob/main/LICENSE) |
| `playwright@agent-marketplace` | Playwright | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli)，`main` | playwright-cli | [Apache-2.0](https://github.com/microsoft/playwright-cli/blob/main/LICENSE) |
| `playwright-best-practices@agent-marketplace` | Playwright 最佳实践 | [currents-dev/playwright-best-practices-skill](https://github.com/currents-dev/playwright-best-practices-skill)，`main` | playwright-best-practices | [MIT](https://github.com/currents-dev/playwright-best-practices-skill/blob/main/LICENSE.md) |

上游作者署名保留在 `author`，市场整理者 `developerName` 为 `hjy`。八个包均提供名称、中文简介、详细说明、能力说明、upstream 网站及 `Developer Tools` 分类。

### Matt 工作流

围绕任务交接、问题诊断、资料研究和 Agent 文档编写。保持用户明确选择的 `main` 跟随方式。

选定目录：`productivity/handoff`、`engineering/diagnosing-bugs`、`engineering/research`、`productivity/writing-for-agents`。

使用 `skills/` 而非仓库根，避免根目录已有的 `.claude-plugin/plugin.json` 优先声明一整套 Skills。

### Anthropic 前端与测试

只加载 `frontend-design` 和 `webapp-testing`，不加载 PDF 或其他 Skills。

- 初始锁定 commit：[`dbd4588f9e1033efb41dad4bef2f7947c8993d44`](https://github.com/anthropics/skills/commit/dbd4588f9e1033efb41dad4bef2f7947c8993d44)。这是本次核对的快照，不声称与旧全局安装内容一致。
- 许可证：[frontend-design / Apache-2.0](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/frontend-design/LICENSE.txt)、[webapp-testing / Apache-2.0](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/webapp-testing/LICENSE.txt)。

webapp-testing 内部使用 Playwright / Python。Anthropic 包只接入 Skill，不安装这些运行依赖；Microsoft CLI 由独立 Playwright 包提供。实际执行网页测试时需按目标项目环境准备依赖。

### Vue 开发技能：一个历史 upstream Bundle

两个 Skills 的原始作者不同，但 Antfu 的历史合集已经同时收录它们，因此可以通过一个 Git source 安装为一个 Plugin，无需在本仓库合并源码。

| Skill | 原始来源 | 合集目录 | 当前快照中的版本 |
| --- | --- | --- | --- |
| vue | [antfu/skills](https://github.com/antfu/skills)，根据 [vuejs/docs](https://github.com/vuejs/docs) 生成 | `skills/vue` | `2026.1.31` |
| vue-best-practices | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) | `skills/vue-best-practices` | `18.0.0`；合集 SYNC.md 记录原始 commit `f3dd1bf4d3ac78331bdc903e4519d561c538ca6a` |

锁定 commit：[`a74f281a27dadc02397bc1a174b0f2c97531b6ae`](https://github.com/antfu/skills/commit/a74f281a27dadc02397bc1a174b0f2c97531b6ae)。两个 `SKILL.md` 与本机旧全局版本一致（忽略 Git 换行差异）。许可证：[合集 MIT](https://github.com/antfu/skills/blob/a74f281a27dadc02397bc1a174b0f2c97531b6ae/LICENSE.md)、[vue-best-practices MIT](https://github.com/antfu/skills/blob/a74f281a27dadc02397bc1a174b0f2c97531b6ae/skills/vue-best-practices/LICENSE.md)。

全文件比对中，29 个本地 Vue 文件与安装快照一致；快照比本机 vue-best-practices 少一篇 `references/perf-avoid-component-abstraction-in-lists.md`。因此这是两个现有 Skills 的历史合集版本，不是旧全局目录的完整镜像；没有补拷该参考文件。

**不能改为跟随最新 main：** Antfu 在 2026-09-25 的[移除 vendored Skills 提交](https://github.com/antfu/skills/commit/e98e476e315f068f72d53bd3afb34fdd4d5851c3)中删除了 vue-best-practices。当前选用删除前的合集快照，后续两个原始 upstream 的更新不会自动进入此包；升级需人工确认一个仍包含两者的来源版本。

关键配置：

```json
{
  "name": "vue-skills",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/antfu/skills.git",
    "path": "./skills",
    "sha": "a74f281a27dadc02397bc1a174b0f2c97531b6ae"
  },
  "skills": ["./vue", "./vue-best-practices"]
}
```

### Vercel Skills 与 Web 设计规范

两个包来自不同 upstream，分别管理。Vercel Skills 当前只加载 `skills/find-skills`；Web 设计规范只加载 `skills/web-design-guidelines`。两者跟随 `main`。

Web 设计规范每次审查还会读取 [Web Interface Guidelines 的 main 规则](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)，接受规则自动变化，不保存本地镜像。

find-skills 上游说明包含 `npx skills add` 的 standalone 安装方式。本机采用 Marketplace / Plugin 管理第三方能力：查找结果可用作来源信息，新增安装通过 Marketplace 入口处理，避免重新生成已清理的 standalone 副本。没有修改 upstream SKILL.md。

### Java / Spring Boot

只加载 `skills/java-spring-boot`，当前 Skill 版本仍为 `3.0.0`。以 `skills/` 为 Plugin 根，避开 upstream 仓库根的 `.claude-plugin/plugin.json`，不加载其他 Java Skills、Agents 或工具。

2026-10-10 核对 upstream [LICENSE](https://github.com/pluginagentmarketplace/custom-plugin-java/blob/main/LICENSE)：第 3(a) 条允许个人、教育和商业使用，3(b) 允许自行修改，3(c) 允许在附带许可证的条件下分发副本。第 4 条要求保留版权、商标和许可证，不冒认作者，不未经许可声称作者背书；4(d) 禁止不附带该许可证进行再许可、出售或转让。这是自定义许可证，不标注为 MIT 或 Apache-2.0。

没有发现明确禁止本市场远程链接的条款，因此采用原生 remote upstream 入口。仓库只保存指针和 metadata，不复制或重新发布 Java 核心源码；使用仍受上游全部条款约束。

### Playwright：Microsoft 官方 CLI Skill

2026-10-10 检查了 OpenAI 当前 [curated Playwright](https://github.com/openai/skills/tree/main/skills/.curated/playwright)：SKILL.md 和 CLI 参考仍写死 `$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh`，wrapper 仍使用未锁版本的 `@playwright/cli`。它尚未适配 Plugin 安装路径。

按用户最终选择，改用 Microsoft 官方 [playwright-cli Skill](https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli)。Plugin 根为远程 `skills/`，只加载 `./playwright-cli`；Codex 调用标识为 **`playwright:playwright-cli`**，替代旧 standalone `playwright`。Skill 直接调用 CLI，参考文档相对于自身目录读取，没有旧 standalone 路径依赖；无需本地 Adapter、symlink、wrapper 或源码补丁。

Skill 与 CLI 运行依赖分开管理。Plugin 安装不会全局安装 npm 包，也不会改动目标项目依赖。已有 CLI 可直接调用；没有全局命令时可使用原生 npm 执行入口：

```powershell
npm exec --yes --package @playwright/cli@latest -- playwright-cli --help
```

CLI 按当前最新版本使用，不统一锁版本。运行前遵循目标项目的 mise / Node 约束；当前 upstream CLI 要求 Node `>=18`。本机验证时 `npx` 曾在返回版本后出现 Windows/libuv 退出错误；上述 `npm exec` 正常退出，并通过真实浏览器冒烟流程。没有切换运行时或修改全局环境。

### Playwright 最佳实践：当前 1.2 结构

旧 standalone 为 `1.1`，本轮升级到 upstream 当前 `1.2`。仓库根下的 `playwright-best-practices/` 包含 SKILL.md 和八类参考目录：`core`、`debugging`、`testing-patterns`、`advanced`、`architecture`、`frameworks`、`infrastructure-ci-cd`、`browser-apis`。

入口用 `source: url` 指向远程仓库根，显式指定 `skills: ["./playwright-best-practices"]`。这样保留上游当前布局及根目录许可证，不需要复制、搬移或锁历史 commit。Codex 不接受 Skill 路径 `./`，因此不用 Skill 自身目录作 Plugin 根再引用 `./`。

该包与 Microsoft Playwright 来自两个 upstream，原生单一 Git source 无法直接合并两套目录，因此保持两个 Plugin。

### 原生适配与版本

Upstream 所选 Plugin 根当前没有 Plugin manifest。Codex 的 Marketplace manifest fallback 在安装缓存生成 `.codex-plugin/plugin.json`，按路径数组发现指定 Skills。缓存可能包含其他 upstream 文件，但不表示这些 Skills 已加载；不执行 upstream 仓库的同步或构建脚本。

若 upstream 后续在这个根目录增加 manifest，它会优先于 fallback，需要重新验证加载范围。CLI 的版本标签 `local` 是 fallback 缓存标签，不是 release 版本。新增五个包跟随 upstream 默认分支 `main`，不锁 tag / SHA；此前 Anthropic、Vue 的快照保持不变，Vue 仍有上述合集兼容性限制。没有 updater、release checker、版本数据库或通用下载器。

## 启用与调用方式

**插件手动选择安装，安装后默认启用，可在 UI 手动 Enable / Disable。** 启用会让 Codex 发现 Skills，不会在会话开始时自动执行。

| Skill 标识 | 调用方式 | 匹配场景 |
| --- | --- | --- |
| `matt-skills:handoff` | **仅手动** | 显式请求任务交接，例如 `$matt-skills:handoff` |
| `matt-skills:diagnosing-bugs` | **条件自动 / 手动** | 复杂 Bug、故障和性能回归诊断 |
| `matt-skills:research` | **条件自动 / 手动** | 研究问题、收集官方资料 |
| `matt-skills:writing-for-agents` | **条件自动 / 手动** | 编写 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 |
| `anthropic-skills:frontend-design` | **条件自动 / 手动** | 新建界面或重新设计现有界面 |
| `anthropic-skills:webapp-testing` | **条件自动 / 手动** | 网页交互测试与浏览器验证 |
| `vue-skills:vue` | **条件自动 / 手动** | Vue 组件、响应式与内置能力 |
| `vue-skills:vue-best-practices` | **条件自动 / 手动** | Vue 开发规范与最佳实践 |
| `vercel-skills:find-skills` | **条件自动 / 手动** | 查找 Skills 与来源 |
| `web-design-guidelines:web-design-guidelines` | **条件自动 / 手动** | 界面规范、可访问性和交互审查 |
| `java-spring-boot:java-spring-boot` | **条件自动 / 手动** | Spring Boot 开发实践 |
| `playwright:playwright-cli` | **条件自动 / 手动** | CLI 浏览器自动化 |
| `playwright-best-practices:playwright-best-practices` | **条件自动 / 手动** | Playwright 测试编写、调试与维护 |

“条件自动”表示 Codex 可以按当前任务和 Skill description 选择调用，不保证每次匹配都会调用，也允许用 `$` 手动选择。handoff 的 upstream `agents/openai.yaml` 设置 `allow_implicit_invocation: false`；其余选定 Skills 未禁止隐式调用，官方默认允许。本仓库只标注实际策略，不改写第三方策略；版本变化后重新核对。

项目级配置可按需增量修改受信任项目的 `.codex/config.toml`，例如：

```toml
[plugins."vue-skills@agent-marketplace"]
enabled = true
```

设为 `false` 禁用整个 Vue 包；其他包使用各自 Plugin 标识。Marketplace 和项目启用状态分开管理。

## 图标暂缓

本轮按用户决定保留默认图标。没有添加无法生效的 `composerIcon` / `logo` 或未使用资产。

官方支持 SVG 图标，但相对路径必须位于 Plugin 根内；纯远程 upstream source 不会合并本市场仓库的自定义资产，远程 fallback 列表还会清除图标路径。以后原生机制支持这种组合时再处理。当前品牌色分别为石板灰、暖棕和灰绿，不使用第三方品牌 Logo。

## 添加、刷新与安装

验证客户端：`codex-cli 0.162.0-alpha.2`，需要支持远程 `git-subdir`、`sha` 和 Marketplace manifest fallback。

首次添加：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
```

已添加的 GitHub 市场刷新后查看可选插件：

```powershell
codex plugin marketplace upgrade agent-marketplace --json
codex plugin list --marketplace agent-marketplace --available --json
```

**按需要选择安装**，以下命令相互独立，不自动安装全部插件：

```powershell
codex plugin add matt-skills@agent-marketplace --json
codex plugin add anthropic-skills@agent-marketplace --json
codex plugin add vue-skills@agent-marketplace --json
codex plugin add vercel-skills@agent-marketplace --json
codex plugin add web-design-guidelines@agent-marketplace --json
codex plugin add java-spring-boot@agent-marketplace --json
codex plugin add playwright@agent-marketplace --json
codex plugin add playwright-best-practices@agent-marketplace --json
```

UI 中打开 **Agent Marketplace**，选择对应的中文插件卡片安装。安装后新建聊天；UI 未刷新时重新打开客户端。

本地开发可用 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。本地和 GitHub 来源共享市场标识，先通过 `marketplace list` 确认来源；切换时手动移除旧市场注册再添加新来源。以上命令会写入日常 Codex 配置，首次验证使用过隔离临时 `CODEX_HOME`。

本轮按用户授权，在日常 Codex 配置实际安装并验证新增包；市场注册已切换到上述本地工作区，既有插件保持启用。新增入口尚未提交 / 推送，因此现在从 GitHub 刷新无法取得本轮变化。以后发布后再用原生命令移除本地市场注册并添加 GitHub 来源；不需要复制安装缓存或 standalone 目录。

### 更新方式

- `marketplace upgrade` 刷新 Git Marketplace 快照；快照变化时，当前官方实现重新获取已配置的插件来源。
- Matt 和新增五个包跟随 `main`，但不后台持续同步。仅 upstream 更新而市场快照不变时，upgrade 可能返回 `upgradedRoots: []`；重复 `plugin add <plugin>@agent-marketplace` 可重新获取 main。
- Anthropic / Vue 已锁定 SHA，重复安装仍获取相同快照，不会自动升级。人工确认新版后才修改 SHA；Vue 新快照必须仍包含所选两个目录。
- 本地路径市场重复 `plugin add` 即可。UI 普通 refresh 不视为源码已更新的保证。

## 手工验收与 standalone 清理

1. 刷新后确认八张卡片，名称与来源表一致；接受默认图标。
2. 按需安装，在仓库外新建聊天，确认 Matt / Anthropic / Vue 分别有 4 / 2 / 2 个 Skills，其余五个包各 1 个。Anthropic 前缀下没有 PDF，Java 包下没有其他 Java Skills。
3. 用 `$` 选择带插件前缀的 Skill 验证真实调用；例如 `$matt-skills:handoff`。确认读取路径位于插件安装缓存，而非旧全局目录。
4. UI Disable 某个包后新建聊天，确认仅该包的带前缀 Skills 不再可用；Enable 后新建聊天确认恢复。

本机已逐个验证并删除 13 个旧 standalone 目录：`diagnosing-bugs`、`handoff`、`research`、`writing-for-agents`、`frontend-design`、`webapp-testing`、`vue`、`vue-best-practices`、`find-skills`、`web-design-guidelines`、`java-spring-boot`、`playwright`、`playwright-best-practices`。每个目录删除前，验证进程临时禁用对应 standalone，确认已安装启用的 Plugin 可独立发现；删除后再次强制 discovery，确认插件仍可用。

`resolving-merge-conflicts` 和旧第三方 `pdf` 已决定放弃，不建立 Plugin、Adapter 或 Legacy 入口。当前执行环境的自动安全检查拒绝了这两个目录的删除（包含改为明确文件清单后的非递归删除尝试），仅返回 `blocked by policy`，未给出具体条款；因此这两项清理**尚未完成**。本轮扫描 `~/.codex/skills` 剩余 `.system`、`pdf`、`resolving-merge-conflicts`。`.system` 和官方 runtime 的 `pdf:pdf` 均未改动。

## 验证记录

2026-10-10，使用隔离 Codex 配置和仓库外工作目录验证：三个远程包分别发现 4、2、2 个指定 Skills；中文 metadata、网站与 upstream SHA 正确；逐个禁用 / 重新启用时，其他包的发现结果保持不变。调用方式标注与下载后的 upstream 策略一致。189 个旧全局 Skill 文件及日常 Codex 配置的文件指纹保持不变，`git diff --check` 通过。全部第三方缓存及临时验证脚本都位于仓库外。

本轮新增验证：实际日常 Codex 安装与启用八个包，仓库外 `skills/list` 发现 13 个目标 Skills，来源均为 Plugin 缓存，已迁移 standalone 不再存在。Microsoft Playwright 的 10 个入口参考链接、Currents 1.2 的 58 个入口参考链接均可读取，两套 Skill / 参考文件没有旧 standalone 路径依赖。使用 mise Node `24.19.0`、npm `11.17.0` 与 CLI `0.1.22`，通过临时测试页的打开、快照和关闭；浏览器与产物位于仓库外，会话已关闭。

桌面卡片展示与每个 Skill 的真实模型自动选用仍按上述步骤手工验收。`skills/list` 及文件读取证明安装、启用、发现和来源，不代表已执行每个 Skill 内部的 Spring Boot 开发、Vue 开发或完整 E2E 测试。没有第三方核心源码进入本仓库。

## 官方依据

核对日期：2026-10-10；官方源码 revision：`165299214855c2e48facf9bb3bc3c0fc277ee639`。

- [Plugin 规范](https://developers.openai.com/plugins/build/plugins)：Marketplace source、UI metadata、多个入口和资产规则。
- [Skills 规范](https://developers.openai.com/codex/skills)：显式 / 隐式调用及默认策略。
- [marketplace.rs](https://github.com/openai/codex/blob/165299214855c2e48facf9bb3bc3c0fc277ee639/codex-rs/core-plugins/src/marketplace.rs)：manifest fallback 与远程列表资产限制。
- [manifest.rs](https://github.com/openai/codex/blob/165299214855c2e48facf9bb3bc3c0fc277ee639/codex-rs/core-plugins/src/manifest.rs)：Skill 路径数组和展示字段。
- [loader.rs](https://github.com/openai/codex/blob/165299214855c2e48facf9bb3bc3c0fc277ee639/codex-rs/core-plugins/src/loader.rs)：所选路径发现和 Git SHA 获取。

本仓库使用 MIT License；第三方内容遵守各自 upstream License。
