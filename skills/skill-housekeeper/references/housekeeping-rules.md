# Housekeeping Rules

GC 判定规则的实现说明。如果脚本行为和这里说的不一致，**以脚本为准**（Code is Doc）。

## 扫描根目录

只扫这些 meta-skill 的 `.state/` 目录：

| Skill | State 目录 |
|---|---|
| `workflow-packager` | `self/skills/workflow-packager/.workflow-packager/` |
| `skill-refiner` | `self/skills/skill-refiner/.skill-refiner/` |

**绝不**扫描或操作：
- 任何 SKILL.md 文件
- 任何 `references/` 或 `scripts/` 目录
- `byted/*/skills/` 下的任何东西
- 仓库外的任何路径
- `~/.cursor`, `~/.claude`, `~/.codex` 等 agent runtime 目录

## Staleness 判定

### Candidate reports（`.workflow-packager/candidates/*.md`）

- 按文件名日期排序（`YYYY-MM-DD.md`）
- 保留最近 K 份（默认 K=5）
- 其余 → **archive**（移到 `.workflow-packager/_archive/<run-date>/`）
- 不删除最新 1 份（即使 K=0 也保护一份）

### Refiner reports（`.skill-refiner/reports/<skill>.md`）

- 每个 skill 通常只有一份，且会被覆盖式更新（不是日期分文件）
- 默认行为：保留全部（K=N）
- 仅当 LLM 明确判断"该 skill 已不存在"时归档（脚本会检查对应 skill dir 是否还在）

### Audit snapshots（`.skill-refiner/audit-YYYY-MM-DD.json`）

- 周度快照，多份累计
- 保留最近 K 份（默认 K=4，约 1 个月）
- 其余 → **archive**

### watch.md

- 解析 markdown 表格行，按 `hits` 列降序排
- 保留 top-N（默认 N=50）
- 被截掉的行写入 `.workflow-packager/_archive/watch-<date>.md` 作为备份
- **保留表头和 thresholds 说明部分不动**

### .state/ 总大小预警

- 单个 meta-skill 的 `.state/` 总大小超过 `--warn-bytes`（默认 50 MB）→ warn 但不动
- 仅作为信号：可能 watch.md 失控、可能某次 build_candidates 写了异常大的报告

## 归档目录结构

```
self/skills/workflow-packager/.workflow-packager/
├── candidates/
│   ├── 2026-05-29.md          # 最近 5 份保留
│   └── ...
├── watch.md                    # 截断后版本（top-N）
└── _archive/
    ├── 2026-05-29-housekeeping/  # 本次清理 run 的归档
    │   ├── candidates-2025-12-01.md
    │   └── candidates-2025-12-08.md
    └── watch-2026-05-29.md      # 被截掉的 watch 行
```

归档目录本身也是 GC 候选 — 默认保留最近 6 个 housekeeping run 的 `_archive/<date>/`；更老的整组 drop。

## --hard-delete 的边界

`--hard-delete` 仅当用户**显式**传入时生效，且：
- 仍然只删 `_archive/` 里的内容
- 仍然不会 `rm -rf` 任何包含 SKILL.md 的目录
- 仍然报告每个真删的路径

## 安全检查清单（脚本启动时硬约束）

1. 当前工作目录或仓库根必须是 `aiops/skills`（通过 `skills.config.json` 检测）
2. 每个待操作的 path 必须 `resolve()` 后仍在仓库根之下
3. 拒绝跨 symlink 操作（如果 `.state/` 里有 symlink，直接跳过那一项）
4. 任何 `--apply` 动作前，先确认目标路径不是 SKILL.md / references/ / scripts/

如果任一检查不通过 → 直接 die 退出，不执行后续动作。

## 与其他元 skill 的关系

| skill | 关系 |
|---|---|
| `workflow-packager` | producer：写 candidates/、watch.md；housekeeper 是它的 GC |
| `skill-refiner` | producer：写 reports/、audit-*.json；housekeeper 是它的 GC |
| `ouro` | 不重叠：ouro 吃外部知识进来，housekeeper 清内部状态出去 |
| `skill-creator` | 不重叠：creator 造新 skill，housekeeper 不删 skill 本身 |
| `skillctl` | 不重叠：skillctl 管 symlink；housekeeper 管 meta-skill 的工作 state |
