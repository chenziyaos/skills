#!/usr/bin/env python3
"""build_report.py — combine skillctl audit + transcript signals into a report.

Output: <this skill dir>/.skill-refiner/reports/<skill-name>.md
Optional: --list-targets prints all skills with a recent score / line count.

This script never edits any SKILL.md. It only writes report files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent  # self/skills/skill-refiner/
REPO_ROOT = SKILL_DIR.parent.parent.parent          # aiops/skills/
SKILLCTL = REPO_ROOT / "skillctl"
REPORTS_DIR = SKILL_DIR / ".skill-refiner" / "reports"
SNAPSHOTS_DIR = SKILL_DIR / ".skill-refiner" / "snapshots"


def run_skillctl_audit(skill_filter: list[str] | None = None) -> dict:
    cmd = [str(SKILLCTL), "audit", "--json"]
    if skill_filter:
        cmd.extend(skill_filter)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(f"skillctl audit failed: {proc.stderr}\n")
        sys.exit(proc.returncode)
    return json.loads(proc.stdout)


def run_transcript_scan(skill_name: str, days: int) -> dict:
    script = SKILL_DIR / "scripts" / "scan_transcripts.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--skill", skill_name, "--days", str(days)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"scan_transcripts failed: {proc.stderr}\n")
        return {"skill": skill_name, "scanned_files": 0, "hits": [], "summary": {}}
    return json.loads(proc.stdout)


SEVERITY_BADGE = {"fail": "[fail]", "warn": "[warn]", "info": "[info]"}


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "_(no findings — doctrine-compliant)_\n"
    lines = []
    for f in findings:
        badge = SEVERITY_BADGE.get(f["severity"], f"[{f['severity']}]")
        lines.append(f"- {badge} **{f['rule']}**: {f['message']}")
        lines.append(f"  - hint: {f['hint']}")
    return "\n".join(lines) + "\n"


def format_transcript(scan: dict) -> str:
    summary = scan.get("summary", {})
    hits = scan.get("hits", [])
    head = (
        f"scanned files: {scan.get('scanned_files', 0)}  |  "
        f"hits: {summary.get('hits_total', 0)}  |  "
        f"tier1: {summary.get('tier1_total', 0)}  |  "
        f"tier2: {summary.get('tier2_total', 0)}\n"
    )
    if not hits:
        return head + "\n_(no mentions in scan window)_\n"

    tier1: list[str] = []
    tier2: list[str] = []
    stats: list[str] = []
    for h in hits:
        for s in h["signals"]:
            line = (
                f"- `{Path(h['file']).name}` turn {s['turn_idx']} "
                f"[{s['kind']}]: {s['snippet']}"
            )
            if s["tier"] == 1:
                tier1.append(line)
            else:
                tier2.append(line)
        if not h["signals"]:
            stats.append(
                f"- `{Path(h['file']).name}` turn {h['hit_turn_idx']}: "
                f"{h['hit_snippet'][:120]}"
            )

    parts = [head]
    parts.append("\n### Tier 1 — High-confidence friction\n")
    parts.append("\n".join(tier1) if tier1 else "_(none)_")
    parts.append("\n\n### Tier 2 — Worth review\n")
    parts.append("\n".join(tier2) if tier2 else "_(none)_")
    if stats:
        parts.append("\n\n### Tier 3 — Mentions without explicit friction\n")
        parts.append("\n".join(stats[:20]))
        if len(stats) > 20:
            parts.append(f"\n_(+{len(stats) - 20} more)_")
    return "\n".join(parts) + "\n"


def format_suggested_edits(audit: dict) -> str:
    findings = audit.get("findings", [])
    if not findings:
        return "_(no automated suggestions — review transcript section manually)_\n"

    lines = ["> Auto-generated from audit findings. LLM should refine each entry into a concrete patch."]
    lines.append("")

    priority_order = [
        ("missing-version", "Add `version: v0.1.0` to frontmatter"),
        ("missing-allowed-tools", "Add `allowed-tools:` to frontmatter (purely additive, low risk)"),
        ("desc-no-when-not", "Append 'Do NOT use for ...' boundary to description"),
        ("desc-no-when", "Reword description to include explicit trigger context"),
        ("desc-too-short", "Expand description to cover when/what/when-not"),
        ("missing-name", "Add `name:` field matching directory name"),
        ("missing-description", "Add `description:` field (highest priority — agent won't trigger without it)"),
        ("frontmatter-missing", "Add YAML frontmatter block at top of SKILL.md"),
        ("no-references", "Extract domain knowledge into references/*.md"),
        ("scripts-without-tests", "Add scripts/test_*.py or eval/ to harden RL loop"),
        ("size-soft", "Consider extracting non-critical sections to references/"),
        ("size-hard", "REQUIRED: move long sections to references/, keep SKILL.md ≤ 100 lines"),
    ]

    by_rule = {f["rule"]: f for f in findings}
    for rule, action in priority_order:
        if rule in by_rule:
            lines.append(f"- [ ] **{action}** — current: {by_rule[rule]['message']}")
    return "\n".join(lines) + "\n"


def existing_decision_log(report_path: Path) -> str:
    if not report_path.exists():
        return "_(no prior decisions)_\n"
    text = report_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"## Decision Log\s*\n(.*?)(?=\n##\s|\Z)", text, re.S)
    if not match:
        return "_(no prior decisions)_\n"
    body = match.group(1).strip()
    return body + "\n" if body else "_(no prior decisions)_\n"


def build_report_for(audit: dict, days: int) -> str:
    skill_name = audit["name"]
    report_path = REPORTS_DIR / f"{skill_name}.md"
    scan = run_transcript_scan(skill_name, days)

    out = []
    out.append(f"# Refinement Report — `{skill_name}`\n")
    out.append(f"- generated: `{dt.datetime.now().isoformat(timespec='seconds')}`")
    out.append(f"- source: `{audit['source']}`")
    out.append(f"- version: `{audit['version'] or 'unset'}`")
    out.append(f"- score: **{audit['score']}/100**")
    out.append(f"- SKILL.md: {audit['skill_md_lines']} lines  (`{audit['skill_md_path']}`)\n")

    out.append("## Static Findings\n")
    out.append("Source: `skillctl audit` (deterministic doctrine compliance)\n")
    out.append(format_findings(audit["findings"]))

    out.append(f"\n## Transcript Signals (last {days} days)\n")
    out.append("Source: `scan_transcripts.py` over Cursor/Claude/Codex local transcripts\n")
    out.append(format_transcript(scan))

    out.append("\n## Suggested Edits\n")
    out.append(format_suggested_edits(audit))

    out.append("\n## Decision Log\n")
    out.append("> Append-only. skill-refiner workflow Step 5 records the human verdict.\n")
    out.append(existing_decision_log(report_path))

    return "\n".join(out)


def list_targets(audit_payload: dict) -> int:
    skills = audit_payload.get("skills", [])
    if not skills:
        print("(no skills discovered)")
        return 0
    skills.sort(key=lambda s: s["score"])
    header = ["SCORE", "LINES", "SOURCE", "VERSION", "NAME"]
    rows = [header]
    for s in skills:
        rows.append([
            f"{s['score']:>3}/100",
            str(s["skill_md_lines"]),
            s["source"],
            s["version"] or "-",
            s["name"],
        ])
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    for idx, row in enumerate(rows):
        print("  ".join(c.ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(header))))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="skill name to report on (omit + --list-targets to see options)")
    parser.add_argument("--list-targets", action="store_true", help="print all skills with score, exit")
    parser.add_argument("--days", type=int, default=30, help="transcript scan window in days (default 30)")
    args = parser.parse_args()

    audit = run_skillctl_audit([args.skill] if args.skill and not args.list_targets else None)

    if args.list_targets:
        return list_targets(audit)

    if not args.skill:
        parser.error("--skill required (or use --list-targets)")

    skills = audit.get("skills", [])
    if not skills:
        sys.stderr.write(f"skill '{args.skill}' not found by skillctl audit\n")
        return 1
    target_audit = skills[0]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report_for(target_audit, args.days)
    report_path = REPORTS_DIR / f"{args.skill}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
