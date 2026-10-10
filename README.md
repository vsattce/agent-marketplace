# agent-marketplace

个人使用的 Codex Plugin / Skill 市场，显示名称为 **Agent Marketplace**。Marketplace 记录可选来源，项目实际启用哪些插件由 Codex 配置控制。

Plugin 按 upstream / Skill Bundle 分组。当前 **Matt Skills** 只包含选定的 4 个 Skills；未来的其他来源分别建立 Plugin。跨 upstream 的“我的常用 Skills”集合暂不实现。

## 当前结构

```text
agent-marketplace/
├── .agents/plugins/marketplace.json
├── AGENTS.md
├── README.md
└── LICENSE
```

本仓库只保存 Marketplace 指针和 metadata，**没有保存第三方 SKILL.md、scripts、references 或 assets**。Codex 从 upstream 获取内容并下载到安装缓存。

## Matt Skills 来源与适配

| 项目 | 值 |
| --- | --- |
| Plugin 标识 | `matt-skills@agent-marketplace` |
| 展示名称 | Matt Skills |
| 上游作者 / 市场整理者 | Matt Pocock / hjy |
| Upstream | [mattpocock/skills](https://github.com/mattpocock/skills) |
| Plugin source path | `skills` |
| 跟随分支 | `main`，upstream 默认分支 |
| License | [upstream MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| 安装策略 | `AVAILABLE`，手动选择安装 |

Marketplace entry 的路径配置：

```json
{
  "name": "matt-skills",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/mattpocock/skills.git",
    "path": "./skills",
    "ref": "main"
  },
  "skills": [
    "./productivity/handoff",
    "./engineering/diagnosing-bugs",
    "./engineering/research",
    "./productivity/writing-for-agents"
  ]
}
```

Codex 原生 Marketplace manifest fallback 在安装缓存中生成 `.codex-plugin/plugin.json`，按 `skills` 数组发现指定目录。数组路径相对于选中的 Plugin 根 `skills/`；只有这 4 个 Skills 被加载，缓存中可以包含其他 upstream 文件。

选择 `skills/` 而非仓库根，是因为 upstream 根已有 `.claude-plugin/plugin.json`，会优先于 Marketplace fallback 并声明一整套 Skills。若 upstream 后续在 `skills/` 下新增 Plugin manifest，需要重新验证选择范围。本仓库无需 adapter、同步脚本或下载器。

CLI 显示的版本 `local` 是 fallback 缓存标签，不是 upstream release 版本。跟随 `main` 时重新安装可能获取未发布变更。

## 启用与调用方式

**插件需要手动安装，安装后默认启用；可以在 Codex UI 手动 Enable / Disable。** 启用后 Codex 会发现这些 Skills，但不会在每次会话启动时自动执行它们。

| Skill 标识 | 调用方式 | 匹配场景 |
| --- | --- | --- |
| `matt-skills:handoff` | **仅手动** | 显式请求任务交接，例如 `$matt-skills:handoff` |
| `matt-skills:diagnosing-bugs` | **条件自动 / 手动** | 复杂 Bug、报错、故障或性能回归诊断 |
| `matt-skills:research` | **条件自动 / 手动** | 要求研究问题、收集官方资料或委派资料调查 |
| `matt-skills:writing-for-agents` | **条件自动 / 手动** | 创建或修改 Skill、AGENTS.md、CLAUDE.md 等 Agent 文档 |

“条件自动”表示 Codex 可以根据 Skill description 和当前任务选择调用，不保证每次匹配都会调用。显式调用可使用 `$` 选择对应的带前缀 Skill。handoff 的 upstream `agents/openai.yaml` 设置 `allow_implicit_invocation: false`；其余三个未设置该字段，官方默认值为 `true`。这些是当前上游的实际策略，本仓库仅标注，不覆盖策略；上游更新后需要重新核对。

项目级启用状态可用原生 `.codex/config.toml` 控制（仅受信任项目加载）：

```toml
[plugins."matt-skills@agent-marketplace"]
enabled = true
```

改为 `false` 可在该项目禁用整个 Bundle；由用户按现有配置增量修改。

## 展示信息与图标限制

Plugin 提供中文简介、详细描述、调用方式和 capabilities，分类为 `Developer Tools`，`developerName` 为 `hjy`，品牌色为石板灰 `#475569`，同时保留 upstream 作者署名。

Codex 支持 SVG `composerIcon` / `logo`，但资产路径必须位于 Plugin 根内。当前根来自 Matt upstream，本市场仓库的自定义资产不会随远程 source 安装；安装前的远程 fallback 列表还会清除资产路径。因此本 Bundle 暂用默认图标，未添加无效资产或同步逻辑。后续自有 Plugin 可在自身 `assets/` 下配置原创图标。

## 添加、安装与更新

验证客户端：`codex-cli 0.162.0-alpha.2`，需要支持远程 `git-subdir` 和 Marketplace manifest fallback。

首次添加 GitHub 市场：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
```

已注册市场则刷新，然后列出并安装 Bundle：

```powershell
codex plugin marketplace upgrade agent-marketplace --json
codex plugin list --marketplace agent-marketplace --available --json
codex plugin add matt-skills@agent-marketplace --json
codex plugin list --marketplace agent-marketplace --json
```

确认 `matt-skills` 安装后 `installed: true`、`enabled: true`。UI 中选择 **Agent Marketplace → Matt Skills → Install**，然后新建聊天；列表未刷新时重新打开客户端。

本地开发可注册 `codex plugin marketplace add E:\WorkSpace\agent-marketplace`。本地与 GitHub 市场共享标识，先用 `codex plugin marketplace list` 确认来源；需要切换时手动移除市场注册再添加目标来源。以上命令会写入日常 Codex 配置，自动验证使用隔离临时 `CODEX_HOME`。

`main` 表示获取时跟随该分支，不表示后台持续同步。更新使用上述原生命令：

- `marketplace upgrade` 刷新 Git Marketplace 快照；快照实际变化时，当前官方实现强制刷新该市场中已配置的插件来源。
- **仅 Matt upstream 更新而市场快照不变时，upgrade 可返回 `upgradedRoots: []`，不会强制刷新插件。** 再执行 `plugin add matt-skills@agent-marketplace` 可重新获取 upstream 并替换安装缓存。
- 本地路径市场直接重复 `plugin add`。UI 普通 refresh 不视为源码已更新的保证。

## 从旧 handoff Plugin 迁移与手工验收

旧 `handoff@agent-marketplace` entry 已由 Matt Bundle 替代。刷新市场不保证删除旧安装或旧配置，本仓库不自动卸载或禁用旧插件。

1. 刷新市场并安装 `matt-skills@agent-marketplace`，检查中文展示信息及调用方式。
2. 在仓库外新建聊天，确认只有 4 个带 `matt-skills:` 前缀的 Skills。明确调用 `$matt-skills:handoff`，确认来源为插件缓存中的 `matt-skills/local/productivity/handoff/SKILL.md`。
3. UI Disable Matt Skills 后新建聊天，确认这 4 个带前缀 Skills 均不可用；Enable 后新建聊天确认恢复。
4. 新聊天中按表中场景测试其余 Skills 的任务匹配与实际调用。handoff 仍需显式调用。
5. 确认新 Bundle 正常后，再由用户手动禁用旧 Handoff Plugin，避免重复来源。

当前全局 `~/.codex/skills` 中的所有 Skills 均保留。独立 `$handoff`、旧插件 `$handoff:handoff` 与新 `$matt-skills:handoff` 可以同时存在；验收选择新前缀。禁用新 Bundle 后，旧来源仍可用属于预期。

## 验证记录

2026-10-10，使用隔离 Codex 配置和仓库外工作目录验证最终 Marketplace entry 的远程安装、发现及中文 metadata，确认恰好加载上述 4 个 Skills。原生配置禁用后发现数为 0，重新启用后恢复为 4；上游调用策略与标注一致。日常 Codex 配置及全局 handoff 的文件指纹保持不变。上游核对 commit 为 `49dd158d1076134a641b33efb035946536778336`，entry 仍跟随 `main`。

发布后的桌面展示、真实模型调用及日常环境迁移需按上述步骤手工验收。所有验证缓存位于仓库外，没有复制第三方核心源码到本仓库。

## 官方依据

规范核对日期：2026-10-10；官方源码 revision：`5ef96ab2785f3ecddf279639eff7b1b42c906fa4`。

- [Plugin 规范](https://developers.openai.com/plugins/build/plugins)：Marketplace source、UI metadata 与资产路径规则。
- [Skills 规范](https://developers.openai.com/codex/skills)：显式 / 隐式调用及 `allow_implicit_invocation` 默认值。
- [marketplace.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/marketplace.rs)：Marketplace manifest fallback 与远程列表资产限制。
- [manifest.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/manifest.rs)：兼容 manifest 的 Skill 路径数组及 UI 字段。
- [loader.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/loader.rs)：指定 Skill 根发现。
- [marketplace_upgrade.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/marketplace_upgrade.rs)：市场快照未变化时跳过升级。

本仓库使用 MIT License；第三方内容适用 upstream License。
