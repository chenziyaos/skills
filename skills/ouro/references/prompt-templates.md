# Ouro — Prompt Templates Index

> Prompt templates are split by context to keep each file focused.

## Files

- `prompt-templates-repo-scoped.md` — 当前仓库场景：DR / 容灾治理 / 数据盘点 / skill 扩展
- `prompt-templates-general-purpose.md` — 更通用、偏 AI 自我成长优化：回答风格、错误防线、prompt 模式、失败复盘、自我收敛

## Quick selection

- 你在处理 **本仓库 / DR / 数据看板 / 容灾方案 / 现有 DR skill 扩展** → 读 `prompt-templates-repo-scoped.md`
- 你在处理 **AI 自我成长 / 回答优化 / 行为治理 / 失败复盘 / prompt 内化** → 读 `prompt-templates-general-purpose.md`

## Most universal prompt

```text
用 $ouro 判断这份材料应该沉淀成 create-skill、extend-skill、update-agent-md、add-rule 还是 skip；不要只做一次性总结，也不要重复造轮子。

材料：
<材料内容>
```
