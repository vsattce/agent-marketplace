# 增强代码审查验证记录

## 范围与执行身份

- 目标：`personal-dev:review` 的模型 helper、包装、显式加载、工作流决策；不是对真实生产项目的性能审计。
- 初始基线：`5c29f101724b0da1c934c6747ed9db3995f8203b`，`main`，工作区干净。
- 主模型：`gpt-6.1-sol / xhigh`，来自当前 thread 本轮 `turn_context`；实际派发名单经已安装技能 helper 校验返回 READY。
- 实现：`implement_review`，`gpt-6-luna / xhigh`；独立验收随后使用另一个 `gpt-6-luna / max`。主模型终审与 Git 收尾。
- 已核实工具：mise Python `3.12.13`，uv `0.9.28`，Codex CLI `0.160.1`。普通 `python` 为 Windows Store 别名，所有 Python 命令使用 `mise which python` 给出的解释器路径，不修改 PATH / 运行时配置。

## 设计可实施性检查

`spec_check`（Luna / max）只读检查 spec、plan 和现有包装：未发现接口或边界阻塞；提醒补充有/无 P0/P1、复核不成立和报告状态的验收场景，已加入计划 Step 6。

## 无技能控制组：5 个独立上下文

共同情境：用户要求审查当前项目、生成报告、尽量多找问题并减少追问；无 Git diff，源码和报告目录可访问，可派发 Luna xhigh/max，但主模型精确身份只有旧配置，缺少本轮可靠证据。候选摘要：A 有限缓存（128 条、TTL 300 秒）；B 每分钟一条健康日志、保留 7 天；C 每 30 秒第三方请求，有超时、最多重试 2 次，配额和生产指标未知；D 每次请求追加 2MB 响应至模块级列表、无清理，约每秒一次。

所有演练禁止实际工具、写入和派生；只要求输出下一步决策、一次性材料清单、范围、等级、生产结论及拟派发安排。控制组 1/2 的“禁止派生”导致个别回答把演练限制理解为正式流程限制；3–5 明确区分拟派发与实际派发，核心情境未变。结果由主模型逐条阅读，不按关键词自动判定。

| 代理 | 起步原文 | 降噪 / 编排观察 |
| --- | --- | --- |
| `control_1` | “开始只读审查。” | A/B P3，C P2；模型身份无法核验却不暂停，拟不委派 |
| `control_2` | “开始” | A/B P3，C P2；直接拟派发 Luna，没有本轮主模型来源验证 |
| `control_3` | “开始正式审查；范围清楚，无需先暂停” | A/B P3，C P2；拟两名审查代理，由主审复核，未安排独立候选复核 |
| `control_4` | “开始只读代码审查，不暂停” | A不报，B低/C中；两名代理分任务，主模型身份未确认仍拟执行 |
| `control_5` | “正式执行会开始：信息足以开展只读审查。” | A不报，B P4/C P3；等级体系不统一，身份未确认仍拟派发 |

5/5 在缺少必需模型来源时继续；多数把正常有界行为列为问题，且缺少统一等级与独立复核机制。5/5 正确识别 D 的代码级无界增长；5/5 没有据摘要声称生产已经被封禁或磁盘异常。新增技能应解决前述实测差异，不为已经稳定的行为堆叠通用警告。

## 现有自动测试基线

命令：

```powershell
$taskPython = (mise which python).Trim()
uv run --python $taskPython --no-python-downloads --with 'PyYAML>=6.0.2,<7' python -B -m unittest discover -s tests -p 'test_personal_dev*.py' -v
```

结果：24 个用例，23 通过，1 个隔离客户端 opt-in 用例跳过；exit 0。

## 实现与自动测试

实现代理先增加 adapter / 包装测试，再实现功能。其记录的 RED 为 34 个用例、11 个预期失败、1 个 opt-in skip；GREEN 为 34 个用例、0 失败、1 个 skip。新增 adapter 的 10 个测试覆盖角色映射、数值版本排序、用户覆写、能力不足、非法字段、兄弟 helper 缺失、输入不变及 CLI 安全输出。

主模型独立执行全量 unittest。第一次有 7 个 `test_sync.py` 错误：默认临时路径为 `C:\Users\ADMINI~1\AppData\Local\Temp`，解析后为 `C:\Users\Administrator\AppData\Local\Temp`，触发既有同步脚本的重定向保护。同步脚本及测试均无本次差异；仅在命令进程内将 TEMP / TMP 指向同一目录的解析后长路径，13 个同步测试全通过，没有改保护规则或全局配置。

一次中间全量执行还有两项 CLI 输出捕获返回 `stdout=None`，原因未确定；随后的独立串行全量执行未复现。没有削弱断言或修改 CLI 代码来绕过此现象。最终命令与结果如下：

```powershell
$taskPython = (mise which python).Trim()
$taskTemp = & $taskPython -B -c 'import tempfile; from pathlib import Path; print(Path(tempfile.gettempdir()).resolve())'
$env:TEMP = $taskTemp
$env:TMP = $taskTemp
uv run --python $taskPython --no-python-downloads --with 'PyYAML>=6.0.2,<7' --with 'tomlkit>=0.13.3,<1' python -B -m unittest discover -s tests
```

最终结果：121 个用例，114 通过，7 个 opt-in 客户端用例跳过，exit 0。跳过项不能算作真实客户端行为通过；本次涉及的 personal-dev 原生加载另行启用并验证。

## 有技能演练：5 个独立上下文

使用与控制组相同的核心情境；代理只读取新 SKILL 和两份 references，不扫描真实项目、不写入、不派发实际审查。主模型阅读完整答案后裁决：

| 代理 | 起步与降噪结果 |
| --- | --- |
| `guided_1` | BLOCKED，缺可靠主模型身份；A/B 不报告，C 无已确认问题，D 为 P1 条件候选；覆盖默认存量源码，安排独立严重候选复核 |
| `guided_2` | BLOCKED，A/B 不报告，C 不定为缺陷，D 为 P1 条件候选；首次混入演练现场工具元数据、额外质疑 xhigh，定向澄清后承认无文件证据并撤回该额外材料要求 |
| `guided_3` | BLOCKED，缺可靠身份；adapter / 解释器属于执行方核验，不能机械要求用户提供；A/B 不报告，C 待证据，D 为 P1 条件候选 |
| `guided_4` | BLOCKED，仅需可靠身份；A/B 不报告，C 无已确认问题，D 为代码级 P1 无界增长机制；生产 OOM 仍取决于负载、时长及容量 |
| `guided_5` | BLOCKED，仅需可靠身份；A/B 不报告，C 量化项待运行验证，D 为 P1 条件风险；无 diff 仍应检查全项目自有源码 |

5/5 在缺必需身份时停止正式派发，5/5 不把 A/B 正常有界行为算缺陷；均没有根据摘要断言生产已 OOM、被封禁或宿主机磁盘异常。`guided_2` 的首轮额外缺口属于演练事实混淆，已保留并纠正，不计为无偏差首次通过。后两次演练明确“题设的已核实名单是模拟事实”，均未重复索要已具备材料。行为演练只证明这些情境下的决策，不证明任意项目或生产运行表现。

## 范围、复核和状态场景

`scenario_review`（独立 Luna / xhigh）读取同一技能，按预检 READY 的假设回答 5 个场景；主模型逐项核对：

1. 指定 `backend/payments`：只审该目录，必要时读直接调用的共用 HTTP client；范围外 UI 问题简提；无生产配额/日志仍可继续静态审查。
2. 只有 P2 和风格建议：跳过独立复核，只简述真实 P2，排除纯风格；覆盖完成为 COMPLETE。
3. P1 候选经独立复核证实有容量上限与清理：记录驳回，不保留虚假的 P1；其余 P2 和覆盖完成可为 COMPLETE。证据不足与证实不成立应区别处理。
4. P0 数据破坏经独立确认且覆盖完成：报告 COMPLETE 并完整保留已确认 P0，不自动修复、不把缺陷等同执行 BLOCKED。
5. 审查中出现缺失关键源码的硬阻塞：停止剩余派发、中断运行审查，集中请求源码，保存 BLOCKED 进度；补齐后只接续未完成/受影响范围，不全量重扫。

5 个决策均符合 spec；没有实际执行这些生产审查。

## 原生隔离加载

原生 Codex 发现阶段先确认两个 personal-dev 入口。首次普通提示捕获失败；诊断发现 localhost provider 请求收到 502，捕获器未收到请求。在测试命令进程内为 loopback 设置 NO_PROXY 后通过，未修改系统代理、日常 CODEX_HOME 或缓存。

```powershell
$taskPython = (mise which python).Trim()
$env:AGENT_MANAGER_CODEX_TESTS = '1'
$env:NO_PROXY = '127.0.0.1,localhost,::1'
$env:no_proxy = $env:NO_PROXY
uv run --python $taskPython --no-python-downloads --with 'PyYAML>=6.0.2,<7' python -B -m unittest discover -s tests -p 'test_personal_dev_loader.py' -v
```

结果：1 个原生隔离用例通过，耗时 1.633 秒，exit 0。实测 Codex CLI 0.160.1：两个入口被发现；普通提示不注入；显式开发入口仍注入；显式 review 注入正文和审查/复核模型标签。fixture 只捕获真实请求上下文并停止客户端，没有实际模型推理或运行 Skill 正文。

## 独立验收与修复计数

`accept_review`（另一独立 Luna / max）初次只读验收确认 helper、手动策略、包装、文档和范围符合 spec，未发现阻塞；当时行为和 loader 证据未完成，明确标为 UNVERIFIED，没有把计划当结果。

主模型随后发现正文缺少 loader 断言要求的两个模型标签；由原实现代理完成定向修复第 1 / 2 轮，明确展示实际“审查模型：”及“复核模型：”格式，未削弱加载断言。上述原生加载通过发生在修复后。

同一独立验收代理完成定向复验：本轮修复 PASS、需求覆盖 PASS、质量 PASS，无阻塞；明确保留加载/行为演练的证据边界、guided_2 偏差和未定位的中间捕获异常，没有重复全量测试。主模型完成累计终审：阅读新技能、adapter、refs、测试与包装/文档差异，确认所有改动对应需求；旧开发技能、Claude/Kimi catalog、sources/lock 均无差异。`git diff --check` 通过。

代码、文档和工程验证已达到交付条件；本记录随提交保存，实际 Git 提交、推送与远端 SHA 核验在随后执行，结果以最终聊天为准。

初次实现不计轮次；当前修复轮次为 1 / 2。仍不声称完成生产性能实测或自动刷新日常安装副本。
