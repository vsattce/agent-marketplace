---
name: check-updates
description: "Read-only version checks for recorded Agent Plugin / Skill upstreams and marketplaces. Only use when explicitly invoked by the user."
---

# 只读检查 Agent 更新

只在用户以 `$check-updates` 或 `$agent-manager:check-updates` 明确选择本 Skill 时执行。普通讨论、会话启动或检测到 Plugin 不触发。只检查，不执行更新。

1. 由当前会话身份识别 Agent。身份不明输出 `BLOCKED`；非 Codex 输出 `UNSUPPORTED AGENT`，不套用 Codex 配置。Codex 时读取 [Codex adapter](../../references/codex.md)，核验当前官方只读命令与 metadata。版本/配置机制不明确时中断对应步骤。
2. 找到真实 agent-marketplace 源码目录：从官方 Marketplace metadata、Plugin 已记录来源或用户指定位置定位。安装缓存的 Plugin 目录不等于源码根；不能确认时报告 `BLOCKED`，不要按相似名字认领来源。读取 `sources.yaml`、`sources.lock.json`、Marketplace catalog 和各 Plugin manifest。
3. 第三方项使用 [check_sources.py](scripts/check_sources.py)：按 sources 中 `repo + path + ref` 查询当前目标 commit 和目录存在性，与匹配 source identity 的 lock commit 比较。helper 使用 GitHub API，只读，不 checkout/fetch/sync。相同 ref 去重，超时和 HTTP 错误逐项报告 UNKNOWN，不换源。固定 SHA 只比较该 SHA，不因 main 前进报告更新；path 不存在为 `UPSTREAM PATH MISSING`；source/lock 不匹配为 UNKNOWN。若需要认证，使用已授权连接器或现有认证，不显示 token。目录变更、网络失败、权限不足不等于上游删除。
4. OWNED Plugin 从源码 manifest/catalog 识别，本仓库当前为 agent-manager，未列入 sources 的未来自有 Plugin 仍由本仓库维护。读当前 branch、HEAD、tracking branch 和 origin。用 `git ls-remote` 查询**已记录对应分支**，不硬编码 main。精确 SHA 相同为 `UP TO DATE`；远端 SHA 存在于本地对象库时用 `merge-base --is-ancestor` 判断 `LOCAL AHEAD` / `REMOTE AHEAD` / `DIVERGED`。对象不足用已确认 GitHub origin 的 compare API；取不到可靠 ancestry 为 UNKNOWN。报告 dirty 状态与判断只覆盖 commit 的边界。禁止 pull / merge / rebase / commit / push。
5. Codex 已安装 Plugin / Marketplace 使用 adapter 的官方只读 list 与 metadata。分别呈现安装版本/缓存、Marketplace snapshot/来源、已配置 upstream 当前目标。只有可靠安装 receipt / snapshot commit 或精确内容证据才判断最新；version 字符串相同不足以证明内容一致。没有 upstream/版本映射或官方 list 隐含刷新副作用时 UNKNOWN 并说明。Marketplace 本地 catalog 内容与 GitHub snapshot 分开；不刷新/upgrade/add/remove。未安装入口标明 available，不当作已安装。
6. 列出 Agent 用户 skills 目录中的非 `.system` standalone Skill，读取入口与已存在 provenance（receipt、明确 repo/path/ref 或所属 Git repo）。有可确认来源才比较，无来源为 `UNKNOWN SOURCE`。不搜索同名项目并认领，不扫描/修改本地会话内容。

输出表格：`Name | Type | Current | Remote | Status | Source`。同名不同来源分别列行，列出完整对象身份；commit 可短显示但保留查询依据。行内或表后说明 UNKNOWN / BLOCKED 原因和数据检查时间。汇总 `Latest`、`Updates available`、`Unknown`；LOCAL AHEAD 单独计数，UPSTREAM PATH MISSING / UNKNOWN SOURCE / BLOCKED 计入 Unknown。版本/路径判断仅针对当前**既定**来源，不推荐其他作者/实现。

全流程只读。允许只读 API/web、list/status、ls-remote。优先避免 fetch；确需时只取 Git metadata、不更新工作区并说明元数据写入，不能调用可能刷新 Plugin/Marketplace 的命令。禁止 sync.py、写 sources/lock/config、更新/安装/删除文件、运行 upstream 脚本及 Git 提交/推送。不生成报告文件，直接在对话输出。
