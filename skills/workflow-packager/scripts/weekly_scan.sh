#!/usr/bin/env bash
# weekly_scan.sh — cron-friendly snapshot for workflow-packager.
#
# Does NOT create any skill. Only:
#   1. Runs build_candidates.py and writes .workflow-packager/candidates/<date>.md
#   2. Accumulates sub-threshold patterns into .workflow-packager/watch.md
#
# Suggested cron:
#   0 10 * * 1 /Users/bytedance/aiops/skills/self/skills/workflow-packager/scripts/weekly_scan.sh >>/tmp/workflow-packager.log 2>&1

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_DIR"

python3 scripts/build_candidates.py --days "${WFP_DAYS:-30}" --min "${WFP_MIN:-3}" --top "${WFP_TOP:-3}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] weekly_scan complete"
