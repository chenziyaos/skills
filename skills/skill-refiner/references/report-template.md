# Report Template — `.skill-refiner/reports/<skill>.md`

每次 `build_report.py --skill <name>` 写出的报告骨架。skill-refiner 的 LLM 编辑环节读这份报告做决策。

## 结构

```markdown
# Refinement Report — <skill-name>

generated: <ISO timestamp>
source: <self|byted>
version: <vX.Y.Z>
score: <0-100>
skill_md_lines: <N>

## Static Findings (from `skillctl audit`)

每条 finding 都来自 doctrine checklist，severity = fail / warn / info。

- [warn] size-hard: SKILL.md is 599 lines (doctrine recommends ≤ 100, hard cap 200)
  - hint: Move long sections into references/*.md and link from SKILL.md
- [info] missing-allowed-tools: ...

## Transcript Signals (last <N> days)

按 friction-signals.md 的 tier 分类。每条引用一个 snippet（≤ 200 chars）。

### Tier 1 — High-confidence friction

- `2026-05-22 14:33` — user `不对，应该先 ...`  (cursor: <uuid>.jsonl turn 47)

### Tier 2 — Worth review

- `2026-05-19 09:12` — 3 retries within 2 minutes (cursor: <uuid>.jsonl turns 12-18)

### Tier 3 — Stats only

- avg turns/case: 14
- avg first-trigger-to-close: 11 turns

## Suggested Edits

> 由 build_report.py 占位，由 LLM 在 skill-refiner workflow Step 4 中填写。
> 每条建议遵守 doctrine.md 的优先级排序：先加法（allowed-tools/version）→ 再描述（when-not）→ 再重构（拆 references）。

- [ ] **Add `allowed-tools` to frontmatter**: <proposed value>
- [ ] **Tighten description boundary**: append "Do NOT use for ...".
- [ ] **Move section X to references/X.md**: lines L1-L2 → references/<filename>.md

## Decision Log

> 用户和 LLM 在 RLHF 闭环里的判断记录。每次刷新报告时保留历史。

- 2026-05-29 - applied: add allowed-tools (approved by user)
- 2026-05-29 - rejected: split SKILL.md (user wants to keep monolithic until v2)
```

## 字段约定

- `generated`：build_report.py 写报告的 ISO 8601 时间
- `score`：来自 `skillctl audit` 0-100
- `skill_md_lines`：行数快照（用于 size 类 finding 的取证）
- `Suggested Edits` 列表：build_report.py 用 audit findings 自动生成占位条目，LLM 在 workflow Step 4 完善细节
- `Decision Log`：append-only；每次刷新报告必须保留历史条目，不允许覆盖

## 命名

每个 skill 一份报告：
```
self/skills/skill-refiner/.skill-refiner/reports/<skill-name>.md
```

snapshot 按周存档：
```
self/skills/skill-refiner/.skill-refiner/snapshots/YYYY-MM-DD.json
```

queue 是当周待人工处理列表：
```
self/skills/skill-refiner/.skill-refiner/queue.md
```
