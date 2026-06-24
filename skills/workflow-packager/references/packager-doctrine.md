# Packager Doctrine — When to Package, In What Shape

## 三种打包形式的判定

| 形式 | 判定启发式 | 典型场景 |
|---|---|---|
| **Skill** | 触发由自然语言决定；流程含 LLM 判断；步骤 5~30；输出是文档/分析/编排 | "review my PR" / "汇总会议" / "审视容灾方案" |
| **Subagent** | 步骤 > 30；需要独立 model 选型 / 独立上下文；可并行多份；产物是长报告或代码 | "deep refactor 整个模块" / "并发跑 10 个候选实验" |
| **Shell-Automation** | 全确定性步骤（git/kubectl/curl/jq/file ops）；无 LLM 判断需求；触发可以是 cron/event | "每天 9 点拉 metric 截图存 OSS" |

判定流程：
1. 看 cluster 里每个 example 的 turn 数中位数
   - ≤ 5 且全是 Bash/file ops → Shell-Automation
   - 6 ~ 30 → Skill
   - \> 30 或显式提到"并行/多份/批量" → Subagent
2. 看 cluster 里是否出现 LLM-must token：`分析 / 解读 / review / 评估 / 建议 / 总结 / 起草`
   - 出现 → 不能是 Shell-Automation，强制 ≥ Skill
3. 看是否含跨工具编排（lark + git + db + ...）
   - 是 → Skill 优于 Shell-Automation

## "应该打包"的强信号

- **同一 query 模式 N≥3 次跨 N≥2 个独立 session**（不只是单 session 反复重试）
- **输入域稳定**：每次的"参数空间"看起来固定（如"汇总会议"参数=日期范围；"容灾盘点"参数=VC 名）
- **每次产出有形**：能描述出"完成的标志"
- **agent 在不同次执行中**走的路径相似（说明工作流是 stable 的）

## "不应该打包"的反信号

- **每次都不一样**：query 表面相似但每次的真实任务结构差异巨大（packaging 会过拟合到第一次）
- **太敏感**：涉及 credentials / 内部决策 / PII —— 黑名单直接 drop（safety-rules.md）
- **太基础**：单 Bash command 能搞定的事不需要 skill；不要为"列出 PR 列表"建 skill
- **重叠 >70%**：已有 skill 覆盖 —— 不要建二份；如有"再细粒度的覆盖"需求，应去 refine 已有 skill
- **一次性**：用户明确说"这次特殊处理一下"

## Scheduling-Mode 维度（与 shape 正交）

蒸馏自 Harness 101 #03。同一个 shape=Skill 可以有三种调度风格，packager 会在报告里给出 `scheduling_hint`：

| Scheduling | 何时推荐 | 关键启发式 |
|---|---|---|
| **Ralph Loop** | 长程任务、多轮迭代、需要 file-state 跨轮持久化 | signature 命中 `循环 / 持续 / loop / 直至完成 / 重复`；或 `turn_count_median ≥ 100` |
| **Plan-then-Act** | 任务可拆分为有序子任务；plan.md / todo.md 作 planner ↔ executor 契约 | signature 命中 `plan / 计划 / 拆解 / todo / 逐项 / checklist / 按步骤` |
| **P/G/E (separate evaluator)** | 工作产品需要二次评审（不是一个 agent 自己说 done） | signature 命中 `review / 评估 / 评测 / 校验 / 审阅 / verify` |
| **single-shot** | 短流程；无 loop/plan/eval 信号 | 默认 |

### 自评 agent 的雷区（Harness 101 #03 明确警告）

**写代码/分析/起草 + 自评 = 过早宣告胜利**。packager 在以下情况会主动加 `self_eval_warning`：

1. `shape=Skill` 且 signature 含 `分析 / 解读 / 起草 / 建议 / writeup`（生产创作型产物）
2. 但 signature **不含**任何 review/eval 动词
3. 调度落到 single-shot

→ 报告里会贴出 warning，建议拆成 Generator + Evaluator 两个 skill 调用（同一对话内分两轮，或在 hooks 里 chain）。

> 例：单个 `code-reviewer` skill 自己写 review 又自己说 done — 反例。
> 改法：`code-reviewer` 产出 review 报告 → 另一个 `review-checker` skill 拿报告 + diff 判合规 → 才能 done。

## "Code is Doc" — references/ 偏指引而非内容

蒸馏自《Agent 的超级进化》一文的反复强调："**与其给 AI 详细文档，不如给它指引让它自己调研**。"原因：

- 文档会过时；代码不会（如果它能跑）
- 复制 500 行进 references/ 等于把那 500 行硬塞进 context 预算
- Agent 用 `grep / read / glob` 当场探查的成本，往往比读静态文档低

落到 `references/` 的写法规范：

| 写法 | 取舍 |
|---|---|
| 优先 | "看 `<repo>/foo/bar.py` 的 `do_thing()` —— 那里写了正解" |
| 优先 | "跑 `./skillctl audit --json` 看 `findings[].rule`，规则名即文档" |
| 慎用 | 复制 API 文档全文（很快过时） |
| 禁用 | 复制对方仓库代码（每次源仓库变更都要 sync；且容易触发法务/版权问题） |

`workflow-packager` 在起草新 skill 的 `references/` 时，建议默认输出一份**指针清单**而不是知识库；只有当目标真的是"沉淀**外部**已消亡知识"时再写实质内容（且此时应该走 `ouro`，不是 packager）。

## 最小 SKILL.md scaffold

供 Phase 4 起草用，所有占位符以 `<...>` 表示：

```markdown
---
name: <kebab-case-name>
description: "<one paragraph: what + when to use + when NOT to use>"
version: v0.1.0
---

# <Title>

## When to use
- <trigger phrase 1>
- <trigger phrase 2>

## When NOT to use
- <boundary 1>
- <boundary 2>

## 工作流
1. <step 1>
2. <step 2>
...

## 不变量
- <invariant: report-only? read-only? scope限制?>
```

起草完后必须：
1. 让用户读一遍 description 是否能描述他/她真实的触发意图
2. 跑 `./skillctl audit <name>` 看分数（目标 ≥ 90）
3. 跑 `./skillctl install` 让三个 agent 都可见

## 反例：用户表面要的 ≠ 真的要

| 表面 query | 真正的需求（更准） | 教训 |
|---|---|---|
| "汇总下我今天的会" | 提取待办 + 找跟我相关的发言 | 不要按 query literal 复制 |
| "看看 PR 的问题" | review 5 项预定义检查 | 看流程，不看 query |
| "把这个翻译成英文" | 翻译 + 适配 audience 语调 | 上下文比动作重要 |

起草 description 时多用"动机"而非"动作"。
