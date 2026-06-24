---
name: multi-perspective-review
description: "多视角评审协议：并行收集工程、安全、UX/DX、战略四个视角的 review，并综合成 H/M/L 决议。Use when the user asks for a broad design/code review with multiple lenses or wants reviewer prompts and a synthesis step. Do NOT use for a single quick review, skill quality auditing, or external knowledge absorption."
version: v0.1.1
allowed-tools: Read, Write
---

# multi-perspective-review

> 用四个视角替代单一 reviewer，降低盲区，再把发现汇总成可执行决议。

## When to use

- “4 视角 review 一下”
- “启动内部 + 外部 reviewer”
- “给我 reviewer prompt / synthesis”
- 中大型设计、方案或代码变更需要系统性输入

## When NOT to use

- 单文件小改动 → 直接 review
- skill 质量审计 → `skill-refiner`
- 外部知识吸收 → `ouro`
- 只想要一个视角 → 直接做，不启动协议

## 四个视角

| 视角 | 关注点 |
|---|---|
| A — Engineering | 质量、测试、性能、可维护性 |
| B — Security & Spec | 安全、合规、边界条件 |
| C — Product UX/DX | 首次上手、日常体验、文档质量 |
| D — Strategy & Architecture | 抽象边界、长期演进、过度工程 |

## 标准工作流

1. 明确 scope / exclude / 背景
2. 内部并行做 A+B
3. 生成 C+D 外部提示词
4. 回收四份报告后做 synthesis
5. 如用户需要，基于 H 项生成 patch plan

外部提示词模板见 [references/external-prompts.md](references/external-prompts.md)。

## 输出契约

最少产出：
- H / M / L 分级清单
- 交叉发现（2+ 视角重合的问题）
- 每条发现的处置建议：`fix / defer / won't-fix`

## 关键约束

- review 阶段只读不改
- H 项应尽量少且足够硬，不把所有问题都打成 blocker
- 外部提示词不得包含敏感信息
- synthesis 必须去重，避免四份报告简单拼接
