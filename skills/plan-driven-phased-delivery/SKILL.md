---
name: plan-driven-phased-delivery
description: "计划驱动分阶段交付：以 plan 文件为中心推进 plan / review / impl prompt / close review / handoff。Use when the user is running a multi-phase delivery process with explicit gates, plan versions, or handoff notes. Do NOT use for one-off small edits, review-only work, or pure git/MR operations."
version: v0.1.1
allowed-tools: Bash, Read, Write
---

# plan-driven-phased-delivery

> 主设计师模式：把设计、执行、评审拆成阶段与角色，通过 plan 文件串起整个交付闭环。

## When to use

- 中大型特性开发（通常 > 5 个文件或 > 3 天）
- 用户要“起草 plan / 修订 plan / 写 impl prompt / close review / handoff”
- 需要设计、实现、评审分离，并且希望有显式 phase gate
- 项目已经把 `plans/` 目录作为协作中心

## When NOT to use

- 单次小改动或一次性排障 → 直接做
- 只需要 review，不需要交付流程 → `multi-perspective-review`
- 纯 git / MR 动作 → `managed-skill-submit`
- 外部知识吸收 → `ouro`

## 角色模型

| 角色 | 职责 |
|---|---|
| 主设计师 | 起草/修订 plan、生成 impl prompt、收尾 handoff |
| Reviewer A/B | 工程与安全视角 review |
| Reviewer C/D | UX 与战略视角 review |
| Impl Agent | 按 impl prompt 实施代码变更 |

## 标准工作流

1. **Phase 1 — Plan v0**：写 `plans/<project>-<wave>.plan.md`
2. **Phase 2 — Review**：发起多视角 review，产出 synthesis
3. **Phase 3 — Plan v1**：吸收 H/M 项并形成决议日志
4. **Phase 4 — Impl Prompt**：生成自包含执行指令
5. **Phase 5 — Batch Exec**：由 impl agent 执行，主设计师只监控与答疑
6. **Phase 6 — Close Review**：对照 plan v1 复核实现
7. **Phase 7 — Handoff**：沉淀交付物、已知遗留、下轮候选

生命周期图见 [references/lifecycle-diagram.md](references/lifecycle-diagram.md)，模板见 [references/templates.md](references/templates.md)。

## Phase gates

- Plan v0：文件已写入且用户确认方向
- Review：4 份视角反馈已回收并完成 synthesis
- Plan v1：无遗留 H 项
- Impl Prompt：指令可分发、范围与禁区清晰
- Batch Exec：build / test / lint 全绿
- Close Review：无 blocker
- Handoff：交付物与遗留记录完整

## 命名约定

```text
plans/
  <project>-<wave>.plan.md
  <project>-<wave>-synthesis.md
  <project>-<wave>-impl-prompt.md
  <project>-<wave>-close-review.md
  <project>-<wave>-handoff-notes.md
```

## 关键约束

- Plan 是 single source of truth
- 主设计师不直接写实现代码
- Impl agent 不改 `plans/`
- Close review 出现 blocker 必须回退到执行阶段修复
