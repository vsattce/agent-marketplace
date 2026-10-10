# 编辑器输入

编辑器只处理已支持的 Plugin 项目开关，不处理 AGENTS.md 编辑、Skill / Plugin 安装或一般配置。Kimi Code 的 Plugin 项目开关整批 `BLOCKED`；发送 `agent: "kimi"` 时编辑器也返回 `KIMI PROJECT-LEVEL CONFIGURATION NOT SUPPORTED`。其他文件操作不通过本编辑器。

Codex 使用下方示例。Claude Code 保持相同请求结构，改为 `agent: "claude"`、`inventory.claude_version: "2.1.296 (Claude Code)"`，Plugin targets 使用 `configuration: "marketplace"`，path 为含 `.claude-plugin/plugin.json` 的真实已安装目录。无需 codex_version。能力与高层覆盖证据见 [Claude 支持边界](claude-support.md)。发给此编辑器的 `requests` 只接受 Plugin 开关；单个 Skill 开关或其他文件动作不能放入输入。混合用户批次由 Skill 层先完整预检，再单独传递其受支持的 Plugin 开关子集。

编辑器从 stdin 读取一个 JSON 对象，输出 JSON 报告；成功 exit 0，BLOCKED exit 2。它不联网、不发现/安装 Plugin、不启动 Harness，也不访问 Git 远端。完整 Plugin 开关批次与只读发现证据由当前显式调用的 Agent 提供，**不是用户需要维护的配置文件**。从现有权威信息整理到 stdin，不为输入创建全局文件或复制完整含密钥的 config。

```json
{
  "agent": "codex",
  "explicit_invocation": true,
  "scope": "project",
  "requests": [
    {"kind": "plugin", "target": "frontend-dev@agent-marketplace", "enabled": true},
    {"kind": "plugin", "target": "common-workflow@agent-marketplace", "enabled": false}
  ],
  "inventory": {
    "complete": true,
    "codex_version": "codex-cli 0.162.0-alpha.2",
    "project_root": "E:\\example\\project",
    "project_config_active": true,
    "project_overrides_effective": true,
    "targets": [
      {
        "kind": "plugin",
        "id": "frontend-dev@agent-marketplace",
        "name": "frontend-dev",
        "path": "E:\\example\\read-only-installed-cache\\frontend-dev\\1.0.0",
        "installed": true,
        "configuration": "local-marketplace"
      },
      {
        "kind": "plugin",
        "id": "common-workflow@agent-marketplace",
        "name": "common-workflow",
        "path": "E:\\example\\read-only-installed-cache\\common-workflow\\1.0.0",
        "installed": true,
        "configuration": "local-marketplace"
      },
      {
        "kind": "skill",
        "id": "frontend-dev@agent-marketplace:vue",
        "name": "vue",
        "path": "E:\\example\\read-only-installed-cache\\frontend-dev\\1.0.0\\skills\\vue\\SKILL.md"
      }
    ]
  }
}
```

示例路径为示意，实际必须来自当前环境。targets 包含全部当前 Plugin / Skill 来源，不能只放用户想改的目标来规避同名歧义；包括 disabled 入口，并分别列出不同来源的同名 Skill。id 必须稳定且精确；Skill 用完整 Plugin identity + Skill identity，standalone 用真实绝对 `SKILL.md` 路径。选择器只匹配精确 id/name/path，不模糊匹配。kind、target、enabled 是请求的全部字段；其他配置语义或写入路径参数被拒绝。

complete、project_config_active、project_overrides_effective 是调用者的**证据断言**，不能凭用户意愿或文件存在填 true。必须依据已有会话/官方只读接口及有效层级，确认完整清单、trusted 项目和根配置能决定本次最终状态。无法确认时保留 false 并报告 BLOCKED。编辑器核对 Git root、实际 Agent `--version`、manifest name 与 Plugin identity、安装范围和文件可编辑性，但不会替代调用者对 live discovery / trust / managed / CLI 限制的取证。Claude 分支另检查项目 settings.local.json 的反向覆盖。

path 只用于只读定位目标。唯一持久化写入位置由 Git root 和 agent 固定为 Codex `.codex/config.toml` 或 Claude `.claude/settings.json`，没有 config-path override。settings.local.json 永远只读。same-name 不按 id 优先消歧；当 selector 同时是另一候选的名字或路径，仍报告多个 Matches。相同目标相同状态去重，相反状态整批拒绝。调用本编辑器前，Skill 层须先对混合批次的所有文件操作完成冲突、路径和支持预检；若任何一步不支持，不调用且不写入。

Codex 依赖 tomlkit 保留 TOML 注释与排版；Claude JSON 分支使用标准库，无需 target 项目的包清单。使用已准备的 Agent 工具环境，缺失时 BLOCKED；不运行会向用户缓存写入的 uv 自动依赖安装流程。shell 调用保持 stdin 真正 JSON 与真实换行，不能拼接不可信 shell 文本。
