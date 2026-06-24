---
name: plan-driven-phased-delivery
description: "计划驱动分阶段交付：以 plan 文件为中心的软件交付生命周期管理，含 plan 起草、多视角 review、修订、impl prompt 生成、batch 执行、close review、handoff。当用户提到分阶段交付、plan v0/v1、起草impl prompt、Phase N、close review、handoff notes、主设计师模式时触发。Do NOT use for: 单次小改动（直接做）、只做review不做交付（用multi-perspective-review）、纯git/MR操作（用managed-skill-submit）。"
version: v0.1.0
allowed-tools: Shell, Read, Write, Task
---

# plan-driven-phased-delivery — 计划驱动分阶段交付

> 主设计师模式：不写代码，只把控设计/计划/进度；impl agent 执行具体实现；reviewer 提供质量反馈。严格 phase gate 保证不跳步。

## When to use

- 中大型特性开发（预估 > 3 天 or > 5 个文件）
- 需要角色分工（设计 / 实现 / 评审分离）
- 用户说"起草 plan"、"写 impl prompt"、"close review"
- 项目已有 `plans/` 目录的工作模式

## When NOT to use

- 单次小改动（< 1 小时）→ 直接做
- 只做 review 不做交付 → `multi-perspective-review`
- 纯 git 操作 → `managed-skill-submit`
- 外部知识吸收 → `ouro`

## 角色模型

| 角色 | 职责 | 谁来演 |
|------|------|--------|
| **主设计师** | 起草 plan、修订、把控进度、不写实现代码 | 当前 agent（长会话） |
| **内部 Reviewer A/B** | 工程 + 安全视角 review | subagent |
| **外部 Reviewer C/D** | UX + 战略视角 review | 外部 agent（用户手动分发） |
| **Impl Agent** | 读 impl prompt 执行具体编码 | 另一个 agent 窗口 |

## 标准工作流

### Phase 1 — Plan v0 起草 ✅ 主设计师执行

产出 `plans/<project>-<wave>.plan.md`：

```markdown
# <Project> — <Wave> Plan v0

## 目标
<本轮要达成的 1-3 个具体目标>

## 范围
- IN: ...
- OUT: ...

## 技术方案
<核心设计决策、架构图、数据流>

## 任务分解
| # | Task | 预估 | 依赖 | 优先级 |
|---|------|------|------|--------|

## 验收标准
1. ...
2. ...

## 风险
| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
```

**Gate**: plan 文件已写入 + 用户确认方向。

### Phase 2 — 多视角 Review ✅ 可委托 multi-perspective-review

对 plan v0 发起 4 视角 review：
- 可直接调用 `multi-perspective-review` skill
- 或手动 spawn A+B，生成 C+D 提示词

产出 `plans/<project>-<wave>-synthesis.md`。

**Gate**: 4 份 review 回收 + synthesis 完成。

### Phase 3 — Plan v1 修订 ✅ 主设计师执行

基于 synthesis 的 H/M 决议修订 plan：
- H 项全部 address（fix or explicitly defer with reason）
- M 项逐条决议（fix / defer / won't-fix）
- 记录 anchor 清单（"这些决定不可逆"）

产出：plan v0 → v1 diff + 决议日志。

**Gate**: plan v1 文件完成 + 无遗留 H 项。

### Phase 4 — Impl Prompt 起草 ✅ 主设计师执行

为 impl agent 生成自包含的执行指令：

```markdown
# <Project> — <Wave> Impl Prompt

## 你是谁
你是 <项目> 的实施 agent。严格按本文件执行，不做额外设计。

## 前置
- 分支：<branch>
- 工作目录：<path>
- 必读上下文：<files>

## 执行清单
### Block A (必须，串行)
1. ...
2. ...

### Block B (必须，可并行)
- ...

### Block C (可选，视时间)
- ...

## 完成标准
- [ ] build pass
- [ ] test pass
- [ ] lint pass

## 禁区
- 不改 plans/ 目录
- 不改不相关模块
- 遇到歧义停下来问，不自己做决定
```

**Gate**: impl prompt 文件完成 + 用户确认可分发。

### Phase 5 — Batch 执行 🧑 需人工分发

用户将 impl prompt 分发给 impl agent。主设计师期间：
- 监控进度（如果 impl agent 在同窗口则直接看）
- 回答 impl agent 的疑问
- 不插手具体实现细节

**Gate**: impl agent 报告"完成" + build/test/lint 全绿。

### Phase 6 — Close Review ✅ 可委托 multi-perspective-review

对实现结果做 4 视角 close review：
- 输入：impl 后的代码 diff + plan v1
- 关注：实现是否对齐 plan、是否引入新问题

产出 `plans/<project>-<wave>-close-review.md`。

**Gate**: 无 H 项（有则回到 Phase 5 修复）。

### Phase 7 — Handoff ✅ 主设计师执行

产出 `plans/<project>-<wave>-handoff-notes.md`：

```markdown
# <Wave> Handoff Notes

## 本轮交付物
- ...

## 已知遗留（Known Issues）
- ...

## 下轮候选（Next Wave Candidates）
- ...

## 技术债记录
- ...
```

**Gate**: handoff 文件完成 + git commit/push。

## 决策速查

```
用户意图 →
  ├─ "起草 plan" → Phase 1
  ├─ "review plan" → Phase 2
  ├─ "修订 plan" → Phase 3
  ├─ "写 impl prompt" → Phase 4
  ├─ "impl agent 跑完了" → Phase 6
  ├─ "收尾/handoff" → Phase 7
  └─ "继续任务" → 检查当前 Phase，推进到下一步
```

## 命名约定

```
plans/
  <project>-<wave>.plan.md           # plan v0 → v1
  <project>-<wave>-synthesis.md      # review 综合
  <project>-<wave>-impl-prompt.md    # impl 指令
  <project>-<wave>-close-review.md   # close review
  <project>-<wave>-handoff-notes.md  # 交接记录
```

`<wave>` 示例：`w0`、`w1`、`w2-batch-a`。

## 关键约束

1. **主设计师不写实现代码** — 只产 plan / prompt / review / handoff
2. **每个 Phase 有明确 Gate** — 不满足不进入下一阶段
3. **Plan 是 single source of truth** — 所有决策记录在 plan 中，不散落在聊天里
4. **Impl agent 不改 plans/** — plans 目录只有主设计师修改
5. **Close review 发现 H 项必须回退修复** — 不能带着 blocker 进 handoff
