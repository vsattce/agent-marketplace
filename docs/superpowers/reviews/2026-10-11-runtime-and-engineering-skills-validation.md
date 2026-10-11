# 三项 Skill 增项验证记录

## 执行基线

- 日期：2026-10-11，Asia/Shanghai。
- 工作目录：`E:\workSpace\agent-marketplace`，当前 main，基线 `43f2cb6`；开工前 tracked / staged / untracked 干净。
- 规格：[spec](../specs/2026-10-11-runtime-and-engineering-skills-design.md)；计划：[plan](../plans/2026-10-11-runtime-and-engineering-skills.md)。
- 主模型：本轮 turn_context 核实为 `gpt-6.1-sol / xhigh`。
- 编码：`/root/implement_runtime_engineering`，`gpt-6-luna / xhigh`。
- 独立验收：`/root/accept_runtime_engineering`，`gpt-6-luna / max`。
- 模型 helper 已返回 READY。修复轮次：1 / 2（普通提示正文误注入检查的测试断言）。
- 正常 PowerShell profile 下，mise 与实际 Python 都为 3.12.13；uv 0.9.28；Codex CLI 0.162.0-alpha.17.2；Claude Code 2.1.296。
- 初始 unittest 147 项，10 个真实 loader 默认跳过；两项失败是旧忽略缓存被当作 Skill、手动策略固定英文句与现有中文正文不符；未启用 Python UTF-8 模式时另有两项 gbk 解码错误。后续仅在本次测试进程设置 UTF-8、规范 TMP / TEMP 和禁止 pycache。

## 规格预检和行为基线

独立验收代理未阅读新产品实现，仅读取项目规则、spec / plan，没有发现交付阻塞缺口。无 Skill 的三个虚构场景原本即符合要求，没有人为制造 RED：

1. 已给 SSH alias、认证可用、明确查 app 容器内存增长：直接连接，先核实目标与容器身份，再读取相关内存证据，不增加安全确认。
2. 两次磁盘计数跨 boot_id，90 GiB 变为 80 GiB：不计算速率，不归因到应用；同一 boot_id 重新采样。
3. SSH 超时，本地 Windows CPU 高：有界检查连接并报告远端证据缺失，不拿本机指标替代目标 Linux。

## 实现与验证

- FastAPI：`fastapi/fastapi@master`，commit `f5c6e9b4f9cadc1bf0f9a1fd672e621206b63007`；完整导入 7 个 Skill 文件及根 LICENSE。
- Docker：`docker/skills@main`，commit `f79172733725e2fd236343ee7b963c446ed85d09`；完整导入 11 个 Skill 文件及根 LICENSE，包含上游 metadata、资产、参考、检查和脚本。
- 首次普通 sync 的 FastAPI 整仓 shallow fetch 超过既有 180 秒超时，未进入 publish，目标快照和 lock 未被写入。未修改日常 fetch 实现或新增导入框架。
- 本轮一次性重试复用旧 lock / 本地旧快照，FastAPI 使用 blob:none / sparse-checkout 获取 Skill 及根许可证，Docker 沿用原 fetch；随后仍由现有 sync 校验和事务发布。输出 `Synchronized 15 Skills; 5 snapshot/record paths changed`。
- 编码代理的导入断言核实：旧 13 条 lock 记录全字段相同，13 项 Skill / license 文件树字节指纹全部相同。主模型实际 diff 也只见 lock 新增两条记录；新快照及许可证的 Git text 属性均为 unset。
- 聚焦测试：sync 20 / 20、agent-manager 13 / 13、personal-dev packaging 3 / 3。同步测试覆盖 engineering-tools 的重复同步无差异、upstream 更新、二进制资源与 LICENSE / NOTICE 字节保留、发布失败恢复和 manifest 目标拒绝。
- 完整验证命令：正常 mise / Python 核验后，在 UTF-8、禁用 pycache 和仓库 TMP / TEMP 的测试进程中启用 `AGENT_MANAGER_CODEX_TESTS=1`、`AGENT_MANAGER_CLAUDE_TESTS=1`，执行 `uv run --python (mise which python) --no-python-downloads --with 'PyYAML>=6.0.2,<7' --with 'tomlkit>=0.13.3,<1' python -B -m unittest discover -s tests -v`。
- 编码代理实际 stdout：`Ran 151 tests in 74.811s`，`OK`，0 failures / 0 errors / 0 skips。包含 Claude 两个新第三方入口完整正文、Codex 两个入口的安装字节与精确注入边界，以及运行诊断双端仅手动加载。
- 初始新增测试的 RED 原始输出未保留，故不作为可复用验证证据，也没有补造失败。最终 GREEN 与独立复验结果可核实。
- 本次稀疏导入不代表网络受限时普通整仓 fetch 已验证成功。

### Codex 长正文捕获

独立验收复现了初始“完整正文 substring”断言失败，并定位到实际 Harness 注入行为：在 `codex exec` 的 provider 请求中，`<path>…</path>` 后的文本精确等于源 `SKILL.md` 前 8,000 个 UTF-8 字节，另有一个包装换行。FastAPI 前缀为 8,000 字符，Docker 因多字节字符为 7,980 字符；剥除 frontmatter 后的正文前缀分别约 7,695 / 7,496 字符。未见截断提示，两项正文尾部均未注入。

完整源文件分别为 10,977 / 12,171 字节，`skills/list` 返回路径的安装文件与源逐字节一致。已排除安装副本丢失、JSON 解析或多字段拼接问题；诊断性 app-server turn/start 验证也观察到相同结果，随后移除该临时扩展，保留既有 CLI fixture 与 discovery RPC。

这是 Codex CLI `0.162.0-alpha.17.2` 当前隔离测试的实测限制，和[官方渐进加载说明](https://learn.chatgpt.com/docs/build-skills)存在表述差异，不作普遍版本保证。验收要求据此补充：保留完整快照 / 安装资源，显式调用核实完整正文或明确的原始字节前缀，并输出 `complete=False` 等准确证据；不把标题存在等同于全文加载，不改上游正文以迎合测试。真实模型继续读取文件未验证。

## 独立验收与主模型终审

独立验收核对了两端 7 Plugin / 23 Skill、版本、两项来源与 lock、快照资源 / 许可证、原内容保护、当前文档和三个运行诊断场景。第 1 轮唯一缺口是 Codex 普通提示检查以“全文不存在”断言会漏掉截断误注入；已改为 `captured_skill_source(ordinary, name) is None`，保留描述可见的自动匹配入口。

编码代理定向运行 `test_codex_loader.CodexLoaderTests.test_new_third_party_plugins_discover_and_inject_skills`，实际输出 `Ran 1 test in 1.640s`、`OK`；独立验收又定向复核该用例，1 / 1 通过，未重复全 suite。独立结论：实现与项目内验证 PASS；Codex 真实模型是否消费全部长正文 UNVERIFIED。没有其他交付阻塞项，累计修复 1 / 2 轮。

主模型已检查实际累计 manifest / catalog / source / lock / 同步代码、测试、运行诊断正文和文档，确认同步代码只增加一项白名单，运行诊断只有正文与 metadata。Git 收尾前再次检查实际差异、临时文件和 `git diff --check`。

未提供真实 SSH 目标与认证，本轮不执行远端实机诊断；隔离 loader 捕获上下文后拒绝推理，不等于真实模型业务流程验收。日常客户端安装副本不在本次修改范围内。

首次失败留下的 `.skill-sync-ss65o0x0` 是本轮暂存副本，受既有 `.skill-sync-*/` 忽略规则覆盖。检查绝对路径后执行的递归清理命令被工具自动审批以 `blocked by policy` 拒绝，未改用其他方式绕过；暂存目录保留且不纳入提交。

两端 fixture 还在仓库 TMP 下生成 `claude/fswatch-probe-*/probe`（21 个一字节探针文件）与 `mise/pnpm/12.4.1/bin_paths-7ac48.msgpack.z`（10 字节）。主模型核实本轮生成时间、准确路径、文件名 / 长度、工作区包含关系及无重定向后，尝试只删除这些文件和空目录的非递归清理，同样被自动审批以 `blocked by policy` 拒绝。两类未跟踪缓存保留，未纳入 Git；不声称 worktree 完全干净。原有忽略缓存也保持原状。
