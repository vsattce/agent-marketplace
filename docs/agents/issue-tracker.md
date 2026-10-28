# Issue tracker: Local Markdown

要求发布、读取或跟踪 Issue 的 Skill 使用本仓库 `.scratch/` 下的 Markdown 文件。

## 文件约定

- 每个功能一个目录：`.scratch/<feature-slug>/`。
- 该流程需要的规格说明放在 `spec.md`。
- 每张 Issue 单独保存为 `issues/<NN>-<slug>.md`，编号从 `01` 开始。
- Issue 开头使用 `Status:` 记录状态：`open`、`claimed` 或 `resolved`。
- 存在依赖时，用 `Blocked by: NN, NN` 引用同目录的 Issue；全部依赖解决后才能开始。
- 评论和讨论追加到文件末尾的 `## Comments` 下。
- 领取任务时设为 `claimed`；完成后记录结果与验证证据，再设为 `resolved`。

## Skill 操作映射

- “发布到 issue tracker”：在对应功能目录下创建规格说明或独立 Issue 文件。
- “获取相关 ticket”：读取用户提供的路径；只有编号时，在对应功能目录解析，存在歧义时确认目标。

## 与现有流程的关系

`personal-dev` 的需求、计划和执行记录继续遵循项目既有目录规则。
Issue 引用已有文档路径，避免重复保存同一份需求或计划。
