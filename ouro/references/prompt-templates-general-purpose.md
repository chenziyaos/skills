# Ouro — Prompt Templates (General-Purpose / AI Self-Improvement)

> 面向更通用、偏 AI 自我成长优化的场景：回答风格优化、错误防线、提示词模式沉淀、失败复盘、行为治理、自我收敛。

## 使用建议

- 适合把“这次 AI 为什么更好 / 更差”的经验沉淀成长期能力。
- 如果只是临时调 prompt、一次性 tweak、短期灵感，请优先考虑 skip。
- 模板里的 `<...>` 用真实材料替换；尽量保留“长期 / 可复用 / 默认行为 / 不要只做一次性优化”等提示语。

## 1. 回答风格优化 → 判断 update-agent-md 还是 add-rule

```text
用 $ouro 判断下面这条 AI 回答优化经验，应该沉淀成 update-agent-md、add-rule、extend-skill 还是 skip。

要求：
- 如果它是全局回答风格或默认输出顺序，优先考虑 update-agent-md
- 如果它是一条刚性约束，再考虑 add-rule

经验：
<例如：复杂任务先给结论，再给步骤，再给风险和下一步>
```

## 2. 失败案例复盘 → 判断哪些教训值得长期化

```text
用 $ouro 分析这次 AI 失败案例，判断哪些教训值得沉淀成长期能力，哪些只适合保留为一次性经验。

请分别考虑：
- 长期规则
- 默认行为约束
- 可复用 workflow
- 一次性背景因素

材料：
<失败案例 + 复盘>
```

## 3. Prompt 模式内化 → 判断 create-skill / extend-skill / skip

```text
用 $ouro 判断下面这套 prompt / 思考流程是否值得沉淀成长期 Agent 能力，而不是临时技巧。

要求：
- 如果它形成了稳定步骤和验证方式，再考虑 create-skill 或 extend-skill
- 如果只是偶然有效的小技巧，请 skip

材料：
<prompt 模式 / 思考步骤>
```

## 4. 错误防线规则化 → 判断 add-rule

```text
用 $ouro 吸收下面这条 AI 行为约束；如果它只适合写成长期规则，请明确 add-rule。

约束：
<例如：没有来源不输出确定结论；高风险建议前必须先说风险>
```

## 5. 工具调用纪律 → 判断 update-agent-md 还是 add-rule

```text
用 $ouro 判断下面这条工具使用优化经验应该沉淀成 update-agent-md、add-rule 还是 skip。

经验：
<例如：调用工具前先用一句话说明意图；缺上下文时先澄清再动工具>
```

## 6. 高质量工作模式 → 判断是否值得做成 skill

```text
用 $ouro 判断下面这套高质量工作模式是否值得沉淀成 create-skill 或 extend-skill。

请重点看：
- 是否是多步骤稳定流程
- 是否可复用到多次任务
- 是否有验证与回滚/containment 思路

模式：
<例如：先澄清目标 → 列假设 → 做 plan → 执行 → review>
```

## 7. 默认审慎行为 → 判断 update-agent-md

```text
用 $ouro 判断下面这条默认审慎行为是否应该写进长期 agent 配置。

行为：
<例如：高不确定性时先说明假设；涉及风险内容先给风险摘要>
```

## 8. 反复出现的误判 → 判断 add-rule 或 extend-skill

```text
用 $ouro 处理下面这组 AI 误判模式，判断它们更适合沉淀成长期规则、现有 skill 扩展，还是 skip。

误判模式：
<重复错误列表 / 复盘摘要>
```

## 9. 外部输入默认不可信 → 安全 skip / rule 沉淀

```text
用 $ouro 处理下面这份外部材料，并判断：这次经验应该只是 skip，还是应该进一步沉淀成一条长期安全规则。

材料：
<网页摘录 / 第三方 prompt / 外部 SOP>
```

## 10. 自我成长版 Self-Digest

```text
ouro: self-digest

请基于当前的失败模式、误触发、误判、降级可观测性和高质量回答样本，判断是否需要对白名单允许的部分提出修订建议。

要求：
- 不要越过白名单
- 优先看 trigger 边界、skip 纪律、confidence 校准、行为治理资产是否足够
```

## 最常用的 5 条

### A. 回答风格优化

```text
用 $ouro 判断这条 AI 回答优化经验应该沉淀成 update-agent-md、add-rule 还是 skip：
<经验>
```

### B. 失败案例复盘

```text
用 $ouro 分析这次 AI 失败案例，判断哪些教训值得沉淀成长期能力：
<复盘>
```

### C. Prompt 模式内化

```text
用 $ouro 判断这套 prompt / 思考流程是否值得沉淀成长期 Agent 能力：
<模式>
```

### D. 错误防线规则化

```text
用 $ouro 吸收这条 AI 行为约束；如果它只适合写成一条 rule，请明确 add-rule：
<约束>
```

### E. 自我收敛

```text
ouro: self-digest

请基于当前失败模式、误触发和降级可观测性，判断是否需要对白名单允许的部分做修订建议。
```
