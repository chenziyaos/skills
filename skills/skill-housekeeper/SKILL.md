---
name: skill-housekeeper
description: "Meta-skill that GC's the local skill workspace — prunes stale candidate reports, truncates bloated watch lists, surfaces oversized state directories. Use when the user asks to 清理/精简/瘦身/GC the skills repo, when periodic housekeeping is due, when watch.md / candidates/ have grown beyond a comfortable size, or after running workflow-packager / skill-refiner for many weeks. Do NOT use to delete actual SKILL.md files (that's a different decision), to touch byted/* skills (those go through the MR flow), or to operate outside this repo. Report-only by default; --apply required to actually delete; never modifies SKILL.md."
version: v0.1.0
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
metadata:
  source: self
  scope: meta
---

# skill-housekeeper

This skill is the `/shit` counterpart to `ouro`'s `/eat`. Where `ouro` ingests external knowledge and `workflow-packager` / `skill-refiner` produce reports, **this skill removes what's no longer useful** — so the repo doesn't grow unbounded.

## Why it exists

Both `workflow-packager` and `skill-refiner` write durable artifacts:

- `self/skills/workflow-packager/.workflow-packager/candidates/YYYY-MM-DD.md` (one per scan)
- `self/skills/workflow-packager/.workflow-packager/watch.md` (append-only accumulation)
- `self/skills/skill-refiner/.skill-refiner/reports/<skill>.md`
- `self/skills/skill-refiner/.skill-refiner/audit-<date>.json` (weekly snapshots)

Without GC, these grow forever. Harness 101 #06 explicitly warns: **offloading to disk is only a win if you also GC the disk**. This skill is that GC.

## When to use

- 用户说 "清理 / 精简 / 瘦身 / housekeeping / GC the skills"
- `watch.md` 已经超过几十行难以扫读
- `.workflow-packager/candidates/` 累计了 > 5 份历史报告
- 跑过 N 周的 `weekly_scan.sh` / `refine_weekly.sh` 之后
- skillctl 仓库整体看上去 `.state/` 目录开始膨胀

## When NOT to use

- 删除 SKILL.md 本身 — 这是 `skillctl uninstall` + 手动决定的事
- 清理 `byted/*/skills/` 下的任何东西 — 走 `managed-skill-orchestrator` 的 MR 流程
- 操作 `~/.claude/` / `~/.cursor/` 等 agent runtime 目录 — 那是 agent 自己的领域
- 清理 transcript（`~/.cursor/projects/.../*.jsonl`）— 那是 agent 的运行日志，不归这里
- 一次性临时文件（`/tmp/...`）— 系统 GC 已经管了

## 不变量

- **report-only by default**：默认只产报告，列出"建议清理的项"。`--apply` 才真删。
- **only inside this repo**：永远不动 `aiops/skills/` 之外的任何路径。
- **never SKILL.md**：永远不删任何 `SKILL.md` 或 `references/` 下的实质内容。
- **stat-driven**：用文件 mtime / size / 行数判断 staleness，不基于"我以为该删"。
- **bounded**：所有清理动作有显式上限（保留最近 K 份 / top-N hits / .... 都有 default）。
- **archived not deleted**：默认 `--apply` 也是把过期的报告移到 `.workspace/archive/<date>/`，不直接 `rm`；用 `--hard-delete` 才真 `rm`。

## 标准工作流

1. 跑扫描：

   ```bash
   python3 self/skills/skill-housekeeper/scripts/clean.py
   ```

   默认 dry-run，输出一份"按类型 + 按 skill 分组的建议清理清单"，包含每项的大小、最后修改时间、建议动作（archive / drop / truncate）。

2. 人/LLM review 清单，根据情况：

   - 整组同意 → `python3 .../clean.py --apply`
   - 个别保留 → `--keep <pattern>`
   - 也想清 audit 历史快照 → `--include audit-snapshots`
   - 极少数情况下要真删（不归档）→ `--apply --hard-delete`

3. 跑完后建议：

   ```bash
   ./skillctl audit                # 确认 SKILL.md 都还在
   ./skillctl verify               # 确认 symlink 健康
   ```

## 默认保留策略

| 类型 | 默认保留 | 可调参数 |
|---|---|---|
| `.workflow-packager/candidates/*.md` | 最近 5 份 | `--keep-candidates N` |
| `.skill-refiner/reports/*.md` | 最近 1 份 / skill | `--keep-reports N` |
| `.skill-refiner/audit-*.json` | 最近 4 份（约 1 个月）| `--keep-audits N` |
| `watch.md` 行数 | top-50 by hits | `--watch-max-rows N` |
| 单个 `.state/` 总大小 | 50 MB warn | `--warn-bytes N` |

## 周度自动巡检

适合配进 cron / hooks：

```bash
self/skills/skill-housekeeper/scripts/clean.py --apply       # 默认 archive
```

不会删 SKILL.md，不会动外部路径；可放心安排周度运行。

## references/

- [`housekeeping-rules.md`](references/housekeeping-rules.md) — 详细的 staleness 判定规则、保留策略推导、归档目录结构。
