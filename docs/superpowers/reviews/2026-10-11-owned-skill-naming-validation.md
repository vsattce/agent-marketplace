# 自有 Skill 命名调整验证记录

- 实现代理：`/root/rename_owned_skills`，gpt-6-luna / xhigh；验收代理：`/root/accept_owned_skill_rename`，gpt-6-luna / max。修复轮次：0 / 2；独立验收与主模型终审通过。
- Python 3.12.13、Node 24.19.0、uv 0.12.3；Codex CLI 0.162.0-alpha.17.2、Claude Code 2.1.296、Kimi Code Desktop 1.0.4。
- 首轮双端隔离全量测试 133 项中 129 通过、4 项因 Claude 测试将当前 2.1.296 与单值 2.1.291 比较而失败。测试改用现有已验证版本集合后复跑：133 项通过，exit 0；未更改产品版本支持范围。

全量测试命令：

```powershell
$taskPython = (mise which python).Trim()
$taskTmp = (Resolve-Path '.skill-sync-plugin-dev-task').Path
$env:TMP = $taskTmp
$env:TEMP = $taskTmp
$env:AGENT_MANAGER_CODEX_TESTS = '1'
$env:AGENT_MANAGER_CLAUDE_TESTS = '1'
uv run --python $taskPython --no-python-downloads --with "PyYAML>=6.0.2,<7" --with "tomlkit>=0.13.3,<1" python -B -m unittest discover -s tests -v
```

- `test_dotdot_sibling_prefix_and_other_drive_escape`：跨盘路径 fixture 定向测试 1 项通过；fixture 选择未挂载盘符，避免触碰映射网络盘。
- `claude plugin validate .` 及两个自有插件校验均 exit 0。
- Kimi ASAR loader：5 项中 4 项通过，在线安装项显式 skip；未把 skip 计为通过。
- 当前旧名搜索只命中 `.configure-project.lock` 兼容路径、本次迁移映射以及历史 spec / plan / review。当前调用、链接、资源路径和名称已同步；普通 `review` 与原生 `/review` 保留其语义。
- 原有 28 份相关 Markdown 的 80 个本地链接和锚点通过；新增 plan 到本记录的链接目标单独确认存在。`git diff --check` 通过。`sources.yaml`、`sources.lock.json` 与第三方快照无差异。
- 客户端 UI 中按 `dev` / `am` 短词搜索的行为未实测。隔离加载和 manifest 校验不代表完成 UI 搜索验收。

## 独立验收与主模型终审

- 独立代理检查了 `git diff HEAD` 所含暂存与未暂存差异，以及三个新文档。需求 PASS、质量 PASS、无阻塞项；未重复运行已具备证据的全量测试。旧 Skill 路径没有作为 Markdown 链接残留，第三方及 sources / lock 未修改。
- 主模型将基线中五个旧 Skill 目录的全部 21 个文件按允许的名称替换逐一与工作区比较：全部一致。仅锁兼容注释、旧调用兼容句和命名字符串按 spec 调整，脚本没有其他逻辑变化；每个资源树完整保留，旧目录均不存在。
- 现行入口的旧名搜索仅剩 `am-config/scripts/configure_project.py` 和对应事务测试中的 `.configure-project.lock`。历史文档、迁移表和本次扫描说明保留原名，普通 review / 原生 `/review` 不属于残留入口。
- 两项 test-only 环境适配已在 spec 记录：使用既有 Claude 已验证版本集合及未挂载跨盘 fixture；产品版本支持范围与路径安全逻辑不变。
- 此记录是提交前的验证快照。Git 收尾由主模型在保存记录后执行，实际提交、推送与远端确认结果在最终聊天报告。
