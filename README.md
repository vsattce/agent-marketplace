# agent-marketplace

个人使用的 Agent Plugin / Skill 整理与分发仓库，以 GitHub 为主仓库，优先使用各平台原生能力。

当前只实现 **Phase 1：Codex Marketplace 测试链路**。市场只列出可选插件，实际安装与启用由 Codex 管理。后续平台为 Claude Code、Kimi Code 和 Antigravity，当前均未适配。

## 当前结构

```text
agent-marketplace/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── marketplace-smoke/
│       ├── plugin.json
│       └── skills/
│           └── marketplace-hello/
│               └── SKILL.md
├── README.md
└── LICENSE
```

- `.agents/plugins/marketplace.json` 是 Codex 原生市场入口，市场标识为 `agent-marketplace`。
- `plugins/marketplace-smoke/plugin.json` 使用官方当前推荐的根目录 manifest；`extensions.com.openai` 只提供 Codex 展示信息。
- 插件从根目录 `skills/` 发现 Skill，无需额外配置 Skill 路径。
- 市场条目的 `source.path` 相对**仓库根目录**解析，当前为 `./plugins/marketplace-smoke`。
- 安装策略为 `AVAILABLE`，添加市场后由用户选择安装。

目前无需额外的 `catalog.yaml`、平台目录、安装器、服务或依赖。

## 环境要求

使用支持自定义 Marketplace 和根目录 `plugin.json` 的 Codex 客户端。先在终端确认当前版本及命令：

```powershell
codex --version
codex plugin marketplace add --help
codex plugin add --help
```

若客户端没有这些命令，使用其插件界面完成安装；若市场或根目录 manifest 不受支持，先由用户更新客户端。项目不安装或切换任何运行时。

## 从 GitHub 添加与安装

**前提：这些文件已提交并推送到 GitHub 的 `main` 分支。** 远程安装读取 GitHub 内容，不会包含本地尚未推送的修改。

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin marketplace list
codex plugin list --marketplace agent-marketplace --available --json
codex plugin add marketplace-smoke@agent-marketplace
codex plugin list --marketplace agent-marketplace --json
```

市场显示名称为 **Agent Marketplace**，测试插件显示名称为 **Marketplace Smoke Test**。安装前应能看到可用条目；安装后应能看到 `installed: true` 和 `enabled: true`。测试插件只有 Skill，不连接外部服务，无需登录第三方服务。

也可在 Codex 插件目录选择该市场，打开测试插件并点击 **Install**。CLI 添加市场后，如果桌面界面尚未出现该来源，重启客户端再检查。不同客户端的自定义来源入口可能不同，以实际插件目录为准。

本仓库自有测试插件允许使用 `main`。以后加入第三方插件时，必须单独锁定其 tag 或 commit，由用户人工确认升级。

## 本地试装

推送之前，可在仓库根目录验证本地来源：

```powershell
codex plugin marketplace add .
codex plugin list --marketplace agent-marketplace --available --json
codex plugin add marketplace-smoke@agent-marketplace
```

本地与 GitHub 来源使用相同市场标识。如果已手工试装本地版本，最终验收远程来源时，先卸载该测试插件并移除本地注册，再添加 GitHub 来源，避免缓存旧安装：

```powershell
codex plugin remove marketplace-smoke@agent-marketplace
codex plugin marketplace remove agent-marketplace
codex plugin marketplace add vsattce/agent-marketplace --ref main
codex plugin add marketplace-smoke@agent-marketplace
```

以上手工命令会写入当前用户的 Codex 配置并安装测试插件。本次自动验证使用临时配置目录。

## Skill 调用与开关验收

1. 在 Codex 插件界面确认测试插件已安装并启用。
2. **在其他目录新建聊天**，避免直接读取本仓库的 Skill 文件。输入 `$`，从 Skill 列表选择 `marketplace-smoke:marketplace-hello`，再发送：

   ```text
   使用 $marketplace-smoke:marketplace-hello 执行 Marketplace 测试。
   ```

3. 确认 Codex 读取的是插件安装缓存中的 `SKILL.md`，最终只输出：

   ```text
   AGENT_MARKETPLACE_SMOKE_OK
   ```

4. 在插件界面 **Disable** 测试插件，再新建聊天，确认该插件 Skill 不再作为可用 Skill 出现。不要在已加载 Skill 的旧聊天里判定禁用效果。
5. 再 **Enable** 测试插件，新建聊天，重新选择并调用 Skill，确认恢复可用。

使用 CLI 时，运行 `codex` 后输入 `/plugins` 打开插件浏览器，再按上述步骤检查和调用。

只有输出标记不能证明安装成功；必须同时确认 Skill 来自安装缓存，以及禁用后不可用、启用后恢复。

### 项目级开关

官方支持在受信任项目的 `.codex/config.toml` 中设置：

```toml
[plugins."marketplace-smoke@agent-marketplace"]
enabled = true
```

改为 `false` 即可在该项目禁用。手工修改前读取现有配置，只新增或修改这个插件条目，保留其他内容；若条目已经存在，修改原条目，避免重复表定义。修改后重新读取，并在新聊天验证。

项目配置可覆盖用户级插件开关。如果 UI 开关与实际可用状态不一致，检查当前项目是否有此覆盖；不把安装状态和启用状态混为一谈。

本仓库不提交项目启用配置，也不实现 `plugin-profile`。

## 验证状态

2026-10-10，使用本机 `codex-cli 0.162.0-alpha.2` 和临时 Codex 配置目录执行了原生 CLI / app-server 验证：

| 验证项 | 结果 |
| --- | --- |
| 添加本地 Marketplace，列出市场及可用插件 | 通过 |
| 原生安装测试插件，安装状态与启用状态读取 | 通过 |
| 从仓库外发现安装缓存中的 Skill，解析无错误 | 通过 |
| 原生配置接口禁用后，Skill 不再被发现 | 通过 |
| 原生配置接口重新启用后，Skill 恢复 | 通过 |
| 增量开关操作保留无关配置，缓存 Skill 与源码一致 | 通过 |
| GitHub 来源添加与安装 | 待文件推送后验收 |
| 桌面 UI 展示、开关与新聊天中的真实 Skill 调用 | 待手工验收 |

自动验证使用独立临时配置，未修改日常 Codex 配置；测试文件未纳入仓库。上述本地结果不代表 GitHub 和 UI 全链路已完成。

Phase 1 通过前，不进入后续 Phase。

## 官方依据

规范核对日期：2026-10-10。

- [Package your plugin](https://developers.openai.com/plugins/build/plugins)：Marketplace 入口、根目录 manifest、市场路径规则、原生 CLI 和项目级开关。
- [Build skills](https://learn.chatgpt.com/docs/build-skills)：`SKILL.md` frontmatter、发现与显式调用。
- [Codex 官方 Marketplace 实现](https://github.com/openai/codex/blob/4bad6d78e9b50f9fa8bd941f1db012ed491ad2da/codex-rs/core-plugins/src/marketplace.rs)：入口路径与市场条目解析。
- [Codex 官方根目录 manifest 实现](https://github.com/openai/codex/blob/4bad6d78e9b50f9fa8bd941f1db012ed491ad2da/codex-rs/core-plugins/src/agent_plugin_manifest.rs)：Agent Plugins schema、默认 `skills/` 和 OpenAI 扩展。
- [Codex 官方 Plugin CLI 实现](https://github.com/openai/codex/blob/4bad6d78e9b50f9fa8bd941f1db012ed491ad2da/codex-rs/cli/src/plugin_cmd.rs)：原生安装和列表命令。

MIT License。当前测试插件为本仓库自有内容。
