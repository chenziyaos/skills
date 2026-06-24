#!/usr/bin/env bash
# refine_weekly.sh — cron-friendly snapshot + queue builder for skill-refiner.
#
# This script NEVER edits SKILL.md. It only:
#   1. Snapshots `skillctl audit --json` into .skill-refiner/snapshots/<date>.json
#   2. Compares with previous snapshot and writes .skill-refiner/queue.md
#      listing skills with regression (score down ≥ 10) or new fail/warn findings.
#
# Example cron line (every Monday 09:00):
#   0 9 * * 1 /Users/bytedance/aiops/skills/self/skills/skill-refiner/scripts/refine_weekly.sh >>/tmp/skill-refiner.log 2>&1
#
# Example launchd plist: see hooks/README.md in the repo root.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../../" && pwd)"
SKILLCTL="$REPO_ROOT/skillctl"

SNAPSHOT_DIR="$SKILL_DIR/.skill-refiner/snapshots"
QUEUE_FILE="$SKILL_DIR/.skill-refiner/queue.md"
TODAY="$(date +%Y-%m-%d)"
SNAPSHOT="$SNAPSHOT_DIR/$TODAY.json"

mkdir -p "$SNAPSHOT_DIR"

if [ ! -x "$SKILLCTL" ]; then
  echo "skillctl not executable at $SKILLCTL" >&2
  exit 2
fi

"$SKILLCTL" audit --json > "$SNAPSHOT" || {
  echo "skillctl audit failed" >&2
  exit 3
}

# Find previous snapshot (most recent dated file that's not today's)
PREV="$(ls -1 "$SNAPSHOT_DIR"/*.json 2>/dev/null | grep -v "/$TODAY.json$" | tail -n 1 || true)"

python3 - "$SNAPSHOT" "${PREV:-}" "$QUEUE_FILE" <<'PY'
import json, sys, datetime, pathlib

cur_path, prev_path, queue_path = sys.argv[1], sys.argv[2], sys.argv[3]
cur = json.loads(pathlib.Path(cur_path).read_text(encoding="utf-8"))
prev = {}
if prev_path:
    prev_data = json.loads(pathlib.Path(prev_path).read_text(encoding="utf-8"))
    prev = {s["name"]: s for s in prev_data.get("skills", [])}

regressions = []
new_issues = []
sticky_low = []
for s in cur.get("skills", []):
    name = s["name"]
    score = s["score"]
    findings = s["findings"]
    fail_warn = [f for f in findings if f["severity"] in ("fail", "warn")]
    p = prev.get(name)
    if p:
        delta = score - p["score"]
        if delta <= -10:
            regressions.append((name, p["score"], score, delta, fail_warn))
        prev_rules = {f["rule"] for f in p["findings"]}
        new_rules = [f for f in findings if f["rule"] not in prev_rules]
        if new_rules:
            new_issues.append((name, new_rules))
    if score < 70:
        sticky_low.append((name, score, fail_warn))

today = datetime.date.today().isoformat()
lines = [f"# skill-refiner queue — {today}", ""]

if regressions:
    lines.append("## Regressions (score down ≥ 10)")
    for name, before, after, delta, fw in regressions:
        lines.append(f"- **{name}**: {before} → {after}  ({delta:+d})")
        for f in fw[:3]:
            lines.append(f"  - [{f['severity']}] {f['rule']}: {f['message']}")
    lines.append("")

if new_issues:
    lines.append("## New findings since last snapshot")
    for name, rules in new_issues:
        lines.append(f"- **{name}**:")
        for r in rules[:3]:
            lines.append(f"  - [{r['severity']}] {r['rule']}: {r['message']}")
    lines.append("")

if sticky_low:
    lines.append("## Persistent low scores (<70)")
    for name, score, fw in sticky_low:
        lines.append(f"- **{name}** ({score}/100)")
    lines.append("")

if not (regressions or new_issues or sticky_low):
    lines.append("_All skills doctrine-compliant or improving. No queue this week._")

pathlib.Path(queue_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {queue_path}")
PY

echo "snapshot: $SNAPSHOT"
