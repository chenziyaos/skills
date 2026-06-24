---
name: skill-guide-writer
description: "为现有 skill / tool / plugin 生成或更新使用指南。Use when the user asks for quick start, full guide, upgrade notes, or developer reference based on local files, existing docs, or public web sources. Do NOT use to invent a new skill contract from scratch or to debug why a skill misfires (use skill-refiner)."
version: v0.2.0
allowed-tools: Read, Grep, Glob, WebFetch, WebSearch, Write
---

# skill-guide-writer

> 面向“已有能力”的文档生成器：把分散的说明、代码、示例整理成用户能直接上手的指南。

## When to use

- 用户要某个 skill / tool / plugin 的 Quick Start
- 用户要完整使用手册、FAQ、升级说明、Developer Reference
- 用户已有旧版指南，需要按新行为增量更新
- 你已经有本地源码、现有文档或公开网页，可以据此整理指南

## When NOT to use

- 还没有现成能力，只是想“设计一个新 skill” → `skill-creator`
- 目标是评估某个 skill 为什么不触发 / 怎么提分 → `skill-refiner`
- 目标是外部知识吸收并沉淀为新 capability → `ouro`
- 用户只是要一个简短口头解释，不需要成体系文档 → 直接回答

## 输入优先级

按以下顺序取证，缺什么补什么：
1. 本地 `SKILL.md` / `references/` / `scripts/` / 测试
2. 仓库内 README、示例命令、变更日志
3. 用户提供的 URL 或公开网页（`WebFetch` / `WebSearch`）
4. 用户补充的现有指南、更新说明或目标受众信息

如果核心事实仍不够，最多做一次打包澄清。

## 标准工作流

### Step 1 — 收集证据
- 先读本地主契约与示例
- 外部资料只作为补充，不覆盖本地已验证行为
- 区分 **证据**（文件/命令/输出）与 **推断**（适用场景/最佳实践）

### Step 2 — 选输出层级
- 默认输出 **L2 + L3**
- 若用户要求“简短/概要” → L1
- 若用户要求“完整/详细/二次开发” → L2 + L3 + L4
- 分层定义见 [references/output-levels.md](references/output-levels.md)

### Step 3 — 生成指南
最少包含：
- 适用对象与前置条件
- 最短成功路径
- 1 个端到端示例
- 常见错误与修复
- 边界：能做什么、不能做什么、该配合谁

### Step 4 — 质量自检
按 [references/quality-rubric.md](references/quality-rubric.md) 检查：
- 覆盖度
- 可操作性
- 一致性
- 增量更新标记是否准确

## 增量更新模式

当用户说“更新指南 / skill 升级了 / 加了新功能”时：
1. 读取现有指南或旧版本说明
2. 对照本地新行为与新增参数
3. 输出完整更新后的文档；必要时用 `[NEW]` / `[CHANGED]` / `[DEPRECATED]` 标注变化
4. 不输出“待补充”占位符；确实缺信息时，用 `> ⚠️ 待确认` 明示

## 输出约束

- 默认 GitHub-flavored Markdown
- 示例优先使用可复制命令或最小输入/输出片段
- 不捏造命令、参数、权限、成功结果
- 若内部文档当前不可访问，明确写“依据不足”，不要假装已验证
- 如用户只要聊天内结果，可直接输出；如用户要文件化文档，可落 Markdown 文件

## References

| File | Purpose |
|---|---|
| `references/output-levels.md` | L1-L4 分层定义与默认输出策略 |
| `references/quality-rubric.md` | 生成后自检 rubric 与增量更新检查项 |
