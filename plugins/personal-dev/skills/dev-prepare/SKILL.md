---
name: dev-prepare
description: 需求与计划准备：仅在用户明确调用时，结合项目规则和代码生成 SPEC / PLAN，统一确认一次后结束，不执行开发；适用于 Codex 和 Claude Code。
disable-model-invocation: true
---

# 需求与计划准备

Only use when explicitly invoked by the user. Codex 使用 `$personal-dev:dev-prepare`，Claude Code 使用 `/personal-dev:dev-prepare`；`$dev-prepare` 是本文的入口简称。普通请求不自动触发。

读取[准备与消费契约](../../references/preparation.md)，以 **prepare 模式**执行：读取当前需求、项目规则和相关代码，生成同一 task-id 下的 `spec.md` / `plan.md`，自行检查一致性后附文件路径，只请求一次“SPEC 是否正确、PLAN 是否正确”的统一人工确认。

SPEC 是业务需求最高约束：`SPEC > PLAN > Coder interpretation`。按需求规模控制文档长度；普通细节根据项目现状裁决，重大未决点在这一次确认中一并列出，不先启动多轮问答。

等待明确确认；确认后只记录 CONFIRMED 并结束。本入口只写本次需求文件，**不执行代码、不派发 Coder、不 commit / push，不自动调用 dev-delegate**。修订、阻塞和输出位置均遵循共用契约。

后续开发由用户另行显式调用 `$dev-delegate`；想跳过文档确认并连续开发时，另用 `$dev-auto`。不从本入口自动切换模式。
