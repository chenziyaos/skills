---
name: competitive-product-analysis
description: "竞品/参考项目深度分析：只读探索目标仓库或公开资料，与当前项目做结构化对比并输出可吸收建议。Use when the user asks to analyze competitors, compare projects, or learn from another implementation. Do NOT use to absorb external knowledge into a new skill (use ouro) or to review your own code quality only."
version: v0.1.1
allowed-tools: Bash, Read, Grep, Write
---

# competitive-product-analysis

> 系统性拆解参考项目的架构和产品设计，与当前项目对比，输出“学什么 / 避什么 / 启发什么”。

## When to use

- “分析下 XX 的实现原理和优势”
- “对比下 XX 项目，看看我们差在哪”
- “参考 XX 的能力，如何也实现”
- 设计阶段需要借鉴外部实现
- 已经分析过多个对象，想做 cross-competitive summary

## When NOT to use

- 想把外部 URL / 文档 / 仓库吸收成新 capability → `ouro`
- 只想 review 自己代码 → 直接 review 或 `multi-perspective-review`
- 目标主要是单篇文档解读，而不是项目对比 → 直接阅读或 `ouro`

## 与 ouro 的边界

| | competitive-product-analysis | ouro |
|---|---|---|
| 输入 | 本地/远程仓库、公开资料 | URL / 文档 / 代码片段 |
| 输出 | 对比报告与行动建议 | skill / rule / config 沉淀 |
| 是否修改当前项目 | 不改，只分析 | 可能生成或修改 artifact |

## 标准工作流

1. 明确对比目标：竞品、当前项目、分析维度
2. 只读探索：目录结构、核心抽象、技术栈、工程实践
3. 结构化对比：优势、劣势、中性差异、可吸收建议
4. 如有多个竞品，再输出 cross-competitive summary

详细报告模板见 [references/report-template.md](references/report-template.md)。

## 关键约束

- 不执行竞品代码、不安装依赖、不修改任何文件
- 每个结论都要能落回具体证据
- Action items 必须可执行，而不是泛泛建议
- 若竞品是内部仓库，结果默认不外传
