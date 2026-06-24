---
name: workflow-packager
description: "Meta-skill that mines local conversation history for repeated workflows and proposes them as new Skills, Subagents, or Shell automations. Use when reviewing recent work to decide what should become reusable automation. Do NOT use to improve an existing skill or to absorb external docs/repos into a new capability."
version: v0.2.1
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
metadata:
  reads:
    - "~/.cursor/projects/*/agent-transcripts/*/*.jsonl"
    - "~/.claude/projects/*/  (best-effort)"
    - "~/.codex/log/*  (best-effort)"
    - "skillctl list output (to dedupe against existing skills)"
  writes:
    - ".workflow-packager/candidates/<date>.md (in this skill directory)"
    - ".workflow-packager/watch.md (in this skill directory)"
---

# workflow-packager

> 生命周期里它负责“发现”：从你反复做的事里，找出最值得沉淀成 skill / subagent / shell automation 的候选。

## When to use

- 回顾最近一段时间的工作，看看什么值得自动化
- 想找“下一个该做成 skill 的流程”
- 周期性跑 transcript mining / weekly scan
- `watch.md` 里某个候选累计到阈值以上

## When NOT to use

- 用户已经想清楚要建什么 skill
- 目标是改进现有 skill
- 只想看 skill 的合规分
- 目标是把外部 URL / 仓库 / 文档吸收成新 capability

## 不变量

- 只产候选表和 watch，不直接创建 skill
- 报告只写在 `.workflow-packager/`
- 单次最多升格 3 个候选
- 全流程离线，无远程服务调用

## 标准工作流

1. **数据采集**：`python3 scripts/mine_patterns.py --days 30`
2. **去重与安全过滤**：`python3 scripts/build_candidates.py --days 30 --min 3`
3. **输出候选表**：给出 signature、频率、推荐形式与理由
4. **用户确认后执行**：选中的候选再分别交给 `skill-creator` / subagent 草案 / shell automation 草案
5. **周期运行**：`scripts/weekly_scan.sh` 只累计 watch 与打印 candidates

## 与同仓元 skill 的边界

| skill | 输入 | 输出 |
|---|---|---|
| `workflow-packager` | transcript 重复模式 | 候选 + watch |
| `ouro` | 外部 URL / 仓库 / 文档 | skill / rule / config artifact |
| `skill-creator` | 用户确认的需求 | 新 skill 的 `SKILL.md` |
| `skill-refiner` | 现有 skill + transcript 摩擦 | 改进报告 |

## 安全护栏

- secrets / PII 不进候选
- `byted/*` 不作为默认落点
- 不直接写 skill 文件，必须经用户确认
- 只做确定性 mining；文档起草由调用本 skill 的 agent 完成

详细启发式与安全规则见：
- [references/signal-patterns.md](references/signal-patterns.md)
- [references/safety-rules.md](references/safety-rules.md)
- [references/packager-doctrine.md](references/packager-doctrine.md)
