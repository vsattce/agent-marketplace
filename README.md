# agent-marketplace

个人使用的 Codex Plugin / Skill 市场。Marketplace 记录可选来源，项目实际启用哪些插件由 Codex 配置控制。

Codex 最小测试链路已通过，测试插件已移除。当前只接入第三方 **handoff**，不实现其他平台、批量迁移或自定义安装器。

## 当前结构

```text
agent-marketplace/
├── .agents/plugins/marketplace.json
├── AGENTS.md
├── README.md
└── LICENSE
```

本仓库只保存 Marketplace 指针和 metadata，**没有保存第三方 SKILL.md、scripts、references 或 assets**。真正的 Skill 由 Codex 从 upstream 获取，下载到 Codex 安装缓存是正常安装行为。

## handoff 来源与适配

| 项目 | 值 |
| --- | --- |
| Plugin 标识 | `handoff@agent-marketplace` |
| Skill 标识 | `handoff:handoff` |
| 作者 | Matt Pocock |
| Upstream | [mattpocock/skills](https://github.com/mattpocock/skills) |
| Upstream path | `skills/productivity/handoff` |
| 跟随分支 | `main`，已核实为 upstream 默认分支 |
| License | [upstream MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| 安装策略 | `AVAILABLE`，由用户选择安装 |

Marketplace entry 的关键字段：

```json
{
  "name": "handoff",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/mattpocock/skills.git",
    "path": "./skills/productivity/handoff",
    "ref": "main"
  },
  "skills": "./."
}
```

Upstream 子目录只有 Skill，没有完整 Plugin manifest。Codex 原生 Marketplace manifest fallback 把 entry 的 metadata 转为兼容 manifest，并在安装缓存中生成 `.codex-plugin/plugin.json`。`skills: "./."` 指向选中的子目录根，兼容 manifest 的递归发现机制可读取这里的 `SKILL.md`。本仓库无需单独的 adapter 目录。

这是已验证的 Codex 原生兼容机制。作者后续若在该目录提供 manifest，Codex 会优先使用 upstream manifest，应重新验证路径与加载行为。

本轮按需求跟随 `main`，未锁定 tag / commit；安装或重新安装时可能获取未发布变更。CLI 显示的版本 `local` 是缺少 upstream manifest version 时的缓存标签，不是 handoff 的 release 版本。

## 添加与安装

本机验证版本：`codex-cli 0.162.0-alpha.2`。客户端需要支持自定义 Marketplace、远程 `git-subdir` 和 manifest fallback。可先检查：

```powershell
codex --version
codex plugin marketplace add --help
codex plugin add --help
```

### GitHub 来源

**前提：相关文件已提交并推送至 GitHub。** 尚未推送时，GitHub Marketplace 无法读取本地新增 entry。

首次添加：

```powershell
codex plugin marketplace add vsattce/agent-marketplace --ref main
```

如果已经注册 GitHub 来源，刷新即可：

```powershell
codex plugin marketplace upgrade agent-marketplace --json
```

然后列出并安装：

```powershell
codex plugin list --marketplace agent-marketplace --available --json
codex plugin add handoff@agent-marketplace --json
codex plugin list --marketplace agent-marketplace --json
```

确认 available 中有 `handoff`，安装后 `installed: true`、`enabled: true`。桌面插件目录中选择 **Agent Marketplace → Handoff → Install** 也可验收；CLI 操作后若 UI 未刷新，重新打开客户端。

### 尚未推送时的本地来源

本地 Marketplace entry 仍然从真实 GitHub upstream 下载 handoff：

```powershell
codex plugin marketplace add E:\WorkSpace\agent-marketplace
codex plugin list --marketplace agent-marketplace --available --json
codex plugin add handoff@agent-marketplace --json
```

本地和 GitHub 来源共享 `agent-marketplace` 标识，先用 `codex plugin marketplace list` 确认现有来源。若需切换，手工移除该市场注册后再添加目标来源：

```powershell
codex plugin marketplace remove agent-marketplace
```

该命令移除市场注册；以上所有安装命令会写入当前用户 Codex 配置。自动验证使用独立临时 `CODEX_HOME`，没有执行这些日常环境操作。

## 更新方式与实际限制

`main` 表示获取内容时跟随 upstream 默认分支，不表示后台持续同步。使用 Codex 原生命令：

```powershell
codex plugin marketplace upgrade agent-marketplace --json
codex plugin add handoff@agent-marketplace --json
```

- `marketplace upgrade` 适用于注册的 **Git Marketplace**，检查并刷新市场仓库快照。若市场快照实际更新，当前官方实现会强制重新获取该市场中已配置插件的来源。
- **仅 mattpocock/skills 更新、agent-marketplace 快照未变化时，upgrade 可返回 `upgradedRoots: []`，不会进入上述强制刷新。** 因此不能保证仅执行 upgrade 就更新 handoff。
- 再执行 `plugin add handoff@agent-marketplace` 会重新拉取 upstream `main` 并替换已安装缓存；本机已实测无需卸载或修改版本号。以此作为明确更新 handoff 的原生操作。
- 本地路径注册的市场不能使用 Git Marketplace upgrade；直接重新执行 `plugin add` 获取 upstream 即可。

更新后新建聊天确认 Skill。UI 普通 refresh 不视为已更新源码的保证。本仓库不实现 updater、版本检查或自动修改 ref。

## 手工最终验收

1. 按上述当前来源流程安装，检查 Plugin 来源 URL、子目录和安装状态。
2. 在仓库外新建 Codex 聊天，通过 `$` 选择 **`handoff:handoff`**，明确调用它生成当前聊天的交接文档。确认读取路径位于 Codex 插件缓存，通常为 `~/.codex/plugins/cache/agent-marketplace/handoff/local/SKILL.md`。
3. UI **Disable** Handoff，另开新聊天，确认 `handoff:handoff` 不再可用；再 **Enable**，新聊天确认恢复并调用。
4. 重新执行 `plugin add handoff@agent-marketplace`，确认仍能发现并调用缓存中的 Skill；未来 upstream 有新内容时，用这个操作验证实际更新。

当前独立全局 `~/.codex/skills/handoff` 会继续存在，可能同时出现 `handoff` 和 `handoff:handoff`。验收时选择带插件前缀的条目。禁用插件后，原独立 `handoff` 仍可用属于预期；本仓库不自动删除、禁用或解决重复来源。

## 自动验证结果

2026-10-10，使用隔离的 Codex 配置目录和仓库外工作目录验证：

| 验证项 | 结果 |
| --- | --- |
| JSON 解析、原生 Marketplace 列表与 manifest fallback | 通过 |
| 从真实 upstream main 安装选定 git-subdir | 通过 |
| 安装缓存 Skill 与 upstream 内容比对 | 一致，仅 Git 换行转换不同 |
| 原生 app-server 发现 `handoff:handoff`，解析无错误 | 通过 |
| 原生配置接口禁用后不可发现、启用后恢复 | 通过，保留无关配置 |
| 重复 plugin add 重新获取并替换缓存 | 通过，隔离缓存探针被替换 |
| Git Marketplace upgrade 的未变化快照 | 原生命令返回 `upgradedRoots: []` |
| 当前全局 handoff 和日常 Codex 配置 | 文件指纹保持不变 |
| 含新 entry 的 GitHub 市场、桌面 UI 与真实模型调用 | 待手工验收 |

Skill 内容比对使用 upstream commit `49dd158d1076134a641b33efb035946536778336` 作为本次验证证据，entry 仍跟随 `main`。临时验证文件及下载内容均在仓库外，未纳入 Git。

## 官方依据

规范核对日期：2026-10-10；官方源码核对 revision：`5ef96ab2785f3ecddf279639eff7b1b42c906fa4`。

- [Package your plugin](https://developers.openai.com/plugins/build/plugins)：当前 manifest / Marketplace 规范及远程 source 示例。
- [CLI reference](https://learn.chatgpt.com/docs/cli/reference)：原生 Marketplace 与 Plugin 操作。
- [marketplace.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/marketplace.rs)：远程来源、子目录和 entry manifest fallback。
- [manifest.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/manifest.rs)：兼容 manifest 路径解析。
- [loader.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/loader.rs)：原生 Git 获取、缓存刷新与 Skill 发现。
- [manager.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/manager.rs)：安装及 upgrade 后强制刷新已配置插件。
- [marketplace_upgrade.rs](https://github.com/openai/codex/blob/5ef96ab2785f3ecddf279639eff7b1b42c906fa4/codex-rs/core-plugins/src/marketplace_upgrade.rs)：市场快照未变化时跳过升级。

本仓库使用 MIT License；第三方内容适用 upstream License。
