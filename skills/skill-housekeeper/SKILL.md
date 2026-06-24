---
name: skill-housekeeper
description: "Meta-skill that prunes stale meta-skill state under this repo. Use when the user asks to clean / slim / GC the skills workspace, when `.workflow-packager` or `.skill-refiner` state has grown over time, or when periodic housekeeping is due. Do NOT use to delete actual SKILL.md files, to touch `byted/*`, or to operate outside this repo. Report-only by default; `--apply` is required for mutations."
version: v0.1.1
allowed-tools: Bash, Read, Edit, Write
metadata:
  source: self
  scope: meta
---

# skill-housekeeper

> `workflow-packager` 与 `skill-refiner` 会不断写 candidates、watch、snapshots 等状态文件；本 skill 负责把这些状态目录维持在可读、可控的范围内。

## When to use

- 用户说“清理 / 精简 / 瘦身 / GC the skills repo”
- `.workflow-packager/candidates/` 历史报告过多
- `.workflow-packager/watch.md` 变得过长
- `.skill-refiner/snapshots/` 累积过多周度快照
- 想做周期性 housekeeping，但又不想碰真正的 skill 源文件

## When NOT to use

- 删除或改动 `SKILL.md` / `references/` / `scripts/` / `tests/`
- 清理 `byted/*/skills/` 或 agent runtime 目录
- 删除 transcript、系统临时文件、或仓库外路径

## 不变量

- **report-only by default**：默认只输出 dry-run 报告
- **only inside this repo**：仅操作 `aiops/skills` 内的状态目录
- **archive first**：`--apply` 默认归档到 `<state>/_archive/<date>-housekeeping/`
- **never SKILL.md**：任何 `SKILL.md` 与真实 source 目录都不在作用范围内

## 当前扫描范围

| Skill | State dir |
|---|---|
| `workflow-packager` | `self/skills/workflow-packager/.workflow-packager/` |
| `skill-refiner` | `self/skills/skill-refiner/.skill-refiner/` |

## 标准工作流

### 1. Dry-run

```bash
python3 self/skills/skill-housekeeper/scripts/clean.py
```

默认只报告：
- 老的 `candidates/YYYY-MM-DD.md`
- 老的 `.skill-refiner/snapshots/YYYY-MM-DD.json`
- 过长的 `watch.md`
- 超阈值的 `_archive/<date>-housekeeping/`

### 2. Apply

```bash
python3 self/skills/skill-housekeeper/scripts/clean.py --apply
```

可调参数：
- `--keep-candidates N`
- `--keep-audits N`
- `--watch-max-rows N`
- `--keep-archive-runs N`
- `--warn-bytes N`

只有显式加 `--hard-delete` 时，才会删除超期 `_archive/` 历史 run。

### 3. 收尾验证

```bash
./skillctl audit
./skillctl verify
```

## 默认保留策略

- `candidates/*.md`：保留最近 5 份
- `.skill-refiner/snapshots/*.json`：保留最近 4 份
- `watch.md`：保留 hit 数最高的 top-50 行
- `_archive/<date>-housekeeping/`：保留最近 6 次 housekeeping run

详细规则见 [references/housekeeping-rules.md](references/housekeeping-rules.md)。
