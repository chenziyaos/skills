# Housekeeping Rules

GC 判定规则的实现说明。如果脚本行为和这里说的不一致，**以脚本为准**。

## 扫描根目录

只扫这些 meta-skill 状态目录：

| Skill | State 目录 |
|---|---|
| `workflow-packager` | `self/skills/workflow-packager/.workflow-packager/` |
| `skill-refiner` | `self/skills/skill-refiner/.skill-refiner/` |

绝不扫描或操作：
- 任何 `SKILL.md`
- 任何 `references/`、`scripts/`、`tests/`
- `byted/*/skills/` 下的任何东西
- 仓库外路径与 agent runtime 目录

## Staleness 判定

### Candidate reports
- 目录：`.workflow-packager/candidates/*.md`
- 文件名按 `YYYY-MM-DD.md` 排序
- 保留最近 K 份（默认 K=5）
- 多余文件归档到 `.workflow-packager/_archive/<date>-housekeeping/`

### Refiner reports
- 目录：`.skill-refiner/reports/<skill>.md`
- 默认保留全部；脚本当前不主动轮转这类覆盖式报告

### Audit snapshots
- 目录：`.skill-refiner/snapshots/YYYY-MM-DD.json`
- 保留最近 K 份（默认 K=4）
- 多余文件归档到 `.skill-refiner/_archive/<date>-housekeeping/`

### watch.md
- 解析 markdown 表格行，按 `hits` 列降序排序
- 保留 top-N（默认 N=50）
- 被截掉的行备份到 `.workflow-packager/_archive/watch-<date>.md`
- 表头与说明段保持不动

### `_archive/` 轮转
- housekeeping run 目录形如 `_archive/YYYY-MM-DD-housekeeping/`
- 默认保留最近 6 次 run
- 更老的 run 只有在 `--apply --hard-delete` 时才会真实删除

## 安全边界

脚本启动前必须满足：
1. 仓库根能通过 `skills.config.json` 校验
2. 每个待操作 path `resolve()` 后仍位于仓库根下
3. 任何 `SKILL.md` 或 source 目录一律拒绝
4. `--hard-delete` 只作用于 `_archive/` 里的旧 run
