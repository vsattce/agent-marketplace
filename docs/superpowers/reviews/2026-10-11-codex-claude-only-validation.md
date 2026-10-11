# Codex 与 Claude Code 支持范围验证记录

- 基线：`main`，`8b805a5e4769eb6251d94e0a7a7b39345309d076`，开始时工作区干净。
- 用户需求：将 Marketplace 维护范围收束为 Codex 与 Claude Code；移除 Kimi 安装入口、专属 loader 和管理适配，并让其他 Harness 使用通用不支持结果。
- 编码代理：`/root/remove_kimi`，gpt-6-luna / xhigh；初次修复轮次：0，当前产品修复第 1 轮（共最多 2 轮）。Claude loader 的旧措辞断言同步不计入产品修复轮次。
- 独立验收代理：`/root/review_dual_client`，gpt-6-luna / max；第 1 轮定向复验通过，需求与质量均为 PASS。
- 环境：Python 3.12.13、Node 24.19.0、uv 0.12.3；Claude Code 2.1.296、Codex CLI 0.162.0-alpha.17.2。

## 验证

使用项目规范绝对路径作为测试进程的 `TEMP` / `TMP`，并启用两个现有隔离 loader 开关：

```powershell
$testTemp = (Get-Location).Path
$env:TEMP = $testTemp
$env:TMP = $testTemp
$env:AGENT_MANAGER_CODEX_TESTS = '1'
$env:AGENT_MANAGER_CLAUDE_TESTS = '1'
uv run --python (mise which python) --no-python-downloads --with 'PyYAML>=6.0.2,<7' --with 'tomlkit>=0.13.3,<1' python -B -m unittest discover -s tests -v
```

首次全量运行 133 项，132 通过、1 项失败。失败是 Claude loader 对隔离项目 `AGENTS.md` 的固定断言仍使用旧句“优先兼容 Claude Code 和当前 Codex”；当前规则已改为“当前仅支持 Claude Code 和 Codex”。仅同步该测试断言后，定向复跑 `test_project_upgrade_entry_and_shared_rules_load`：1 项通过，exit 0。完整套件没有在这项测试断言更新后重跑，因此不将两次结果表述为一次全量通过。

`git diff --check` 通过。对当前产品文档、Marketplace 和自有 Plugin 源码搜索 Kimi / Gemini 及旧文件路径无命中；测试中的命中仅用于确认旧 manifest 不存在、同步不会重建入口，以及其他 Harness 返回通用 BLOCKED。隔离 Claude loader 创建的 `claude/fswatch-probe-*` 文件已核验并清理。

## 验收边界

首轮独立验收发现 Claude 来源指南迁移遗漏了指令合并、祖先继承及 exclusions / managed / 项目指令设置。第 1 轮仅补回这些原有语义；独立定向复验确认 ADDRESSED，未发现新阻塞。主模型已检查累计差异、入口与引用、验证证据及范围外修改，终审通过。来源配置、锁文件、第三方快照及历史记录未改动。

Codex 与 Claude 隔离 loader 及当前相关 unittest 已覆盖；Kimi loader 已随产品入口移除，未执行 Kimi 客户端测试。未验证客户端桌面 UI 行为。文档修复未重复运行全量测试或 loader。
