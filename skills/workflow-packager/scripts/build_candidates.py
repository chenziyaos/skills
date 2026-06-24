#!/usr/bin/env python3
"""build_candidates.py — turn mining output into a reviewed candidates table.

Pipeline:
  1. Run mine_patterns.py to get clusters
  2. Pull existing skills (skillctl list + reading SKILL.md description)
  3. For each cluster:
     a. Safety filter (secrets / PII / one-off markers) — drop or redact
     b. Overlap check vs existing skill descriptions (Jaccard); >=0.7 → "covered", skip
     c. Recommend shape: Skill / Subagent / Shell-Automation
  4. Sort by score = session_count * 2 + count
  5. Write top-N candidates to .workflow-packager/candidates/<date>.md
  6. Accumulate < min_occurrences clusters into .workflow-packager/watch.md
     (additive: a cluster appearing twice in different runs gets counted twice)

This script writes only into the skill's own .workflow-packager/ subdirectory.
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


SKILL_DIR = Path(__file__).resolve().parent.parent  # self/skills/workflow-packager/
REPO_ROOT = SKILL_DIR.parent.parent.parent          # aiops/skills/
SKILLCTL = REPO_ROOT / "skillctl"
STATE_DIR = SKILL_DIR / ".workflow-packager"
CANDIDATES_DIR = STATE_DIR / "candidates"
WATCH_FILE = STATE_DIR / "watch.md"


# Safety filters (see references/safety-rules.md)
SECRET_KEYWORDS = [
    "password", "passwd", "api_key", "api-key", "api token", "access_token", "access-token",
    "refresh_token", "bearer", "private_key", "private-key", "credential", ".env",
    "信用卡", "银行卡", "身份证",
]
SECRET_RE = [
    re.compile(r"\b1[3-9]\d{9}\b"),                      # CN mobile
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                 # AWS access key
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),         # email
]
ONE_OFF_HINTS = ("这次", "这一次", "仅这次", "just this once", "ad hoc", "临时", "特殊处理")


def has_secret(text: str) -> bool:
    low = text.lower()
    for kw in SECRET_KEYWORDS:
        if kw in low:
            return True
    return any(pat.search(text) for pat in SECRET_RE)


# Detect "this is really external knowledge absorption, not a workflow" → route to ouro.
URL_RE = re.compile(r"https?://\S+", re.I)
GIT_REPO_RE = re.compile(r"(?:github\.com|code\.byted\.org|gitlab\.com)/\S+", re.I)
EXTERNAL_DOC_HINTS = ("吞噬", "吸收", "absorb", "ingest", "digest")


def is_ouro_candidate(text: str) -> str:
    """If the cluster looks like an external-knowledge absorption task, return why; else ''."""
    if URL_RE.search(text):
        return "samples contain URL(s)"
    if GIT_REPO_RE.search(text):
        return "samples reference external git repo"
    low = text.lower()
    for hint in EXTERNAL_DOC_HINTS:
        if hint in low:
            return f"samples contain absorption verb '{hint}'"
    return ""


def is_one_off(text: str) -> bool:
    low = text.lower()
    return any(hint in low for hint in ONE_OFF_HINTS)


def redact(text: str) -> str:
    out = text
    for pat in SECRET_RE:
        out = pat.sub("[REDACTED]", out)
    return out


# --- skillctl integration ---

def existing_skill_descriptions() -> list[tuple[str, set[str]]]:
    """Return [(skill_name, token_set_of_description), ...]."""
    proc = subprocess.run(
        [str(SKILLCTL), "audit", "--json"], capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"warning: skillctl audit failed; overlap dedupe disabled\n{proc.stderr}\n")
        return []
    payload = json.loads(proc.stdout)
    out: list[tuple[str, set[str]]] = []
    for s in payload.get("skills", []):
        skill_md = Path(s["skill_md_path"])
        # Reuse the lightweight token logic
        desc = _read_description(skill_md)
        toks = _tokens(desc + " " + s["name"])
        out.append((s["name"], set(toks)))
    return out


DESC_RE = re.compile(r"^description:\s*(.+?)(?:\n[a-z_-]+:|^---)", re.S | re.M)
EN_TOK = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")
ZH_TOK = re.compile(r"[\u4e00-\u9fff]{2,}")

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on", "at", "by", "with",
    "is", "are", "was", "were", "be", "do", "does", "did", "use", "uses", "when", "this",
    "from", "into", "as", "if", "then", "than", "so", "not", "yes", "skill",
    "我们", "你们", "他们", "现在", "需要", "可以", "应该", "已经", "什么", "怎么", "为什么",
    "如何", "这个", "那个", "这些", "那些", "时候", "地方", "哪个", "哪里", "一下", "一些",
    "请帮", "帮我", "给我", "麻烦",
}


def _read_description(skill_md: Path) -> str:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    front = text[3:end]
    parts: list[str] = []
    capturing = False
    for line in front.splitlines():
        if line.startswith("description:"):
            capturing = True
            parts.append(line.split(":", 1)[1].strip().strip('"\''))
        elif capturing and (line.startswith(" ") or line.startswith("\t")):
            parts.append(line.strip())
        elif capturing:
            break
    return " ".join(parts)


def _tokens(text: str) -> list[str]:
    text = text.lower()
    raw = EN_TOK.findall(text) + ZH_TOK.findall(text)
    return [t for t in raw if t not in STOPWORDS and len(t) >= 2]


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# --- shape recommendation ---

LLM_VERBS = {
    "分析", "解读", "review", "评估", "建议", "总结", "起草", "理解", "解释",
    "writeup", "explain", "summarize", "analyze", "critique", "评测", "深度",
}
DET_TOOLS = {"Shell", "Read", "Write", "Edit", "Glob", "Grep", "MultiEdit"}
SUBAGENT_HINTS = {"batch", "parallel", "并行", "批量", "多份", "并发"}


def recommend_shape(cluster: dict) -> tuple[str, str]:
    sig = set(cluster.get("signature", []))
    tools = set(cluster.get("tool_traces", []))
    turns = cluster.get("turn_count_median", 0)
    if sig & SUBAGENT_HINTS or turns > 30 * 60:  # 30+ very long sessions
        return ("Subagent", "long-horizon / parallel hints in signature or median turns > 1800")
    deterministic = tools and tools.issubset(DET_TOOLS | {""})
    llm_needed = bool(sig & LLM_VERBS)
    if deterministic and not llm_needed and turns <= 10:
        return ("Shell-Automation", "all deterministic tools, no LLM verbs in signature, short flow")
    if llm_needed:
        return ("Skill", f"signature contains LLM verb(s): {sorted(sig & LLM_VERBS)}")
    return ("Skill", "default: natural-language trigger + multi-step flow")


# --- scheduling-mode hint (orthogonal to shape; per Harness 101 #03) ---
#
# The same shape can be scheduled three different ways:
#   * Ralph Loop   — single agent in a stop-hook loop, file-state as durable memory.
#                    Best for long-horizon work where each turn's product feeds next.
#   * Plan-then-Act— plan.md (or todo.md) is the contract between planner and executor;
#                    executor reads plan, ticks items off, defers ambiguity back to plan.
#   * P/G/E        — Planner / Generator / Evaluator are SEPARATE agent invocations,
#                    because Harness 101 #03 explicitly warns: self-evaluating agents
#                    over-declare victory. Use when the work product needs review.

RALPH_LOOP_HINTS = {"循环", "持续", "loop", "继续直至", "until done", "long-horizon", "重复", "反复"}
PLAN_ACT_HINTS = {"plan", "计划", "拆分", "拆解", "todo", "逐项", "分步", "checklist", "清单", "按步骤"}
EVAL_HINTS = {"review", "评估", "评测", "校验", "verify", "judge", "rate", "score", "审阅", "审查", "复核"}
EVAL_NEEDED_DOMAINS = {"分析", "解读", "建议", "writeup", "起草"}  # work products that need a 2nd eye


def recommend_scheduling(cluster: dict) -> tuple[str, str, str]:
    """
    Returns (mode, reason, self_eval_warning).
    self_eval_warning is empty unless the cluster mixes 'work product' with 'evaluation'
    in a single shape=Skill — see Harness 101 #03.
    """
    sig = set(cluster.get("signature", []))
    turns = cluster.get("turn_count_median", 0)

    needs_eval = bool(sig & EVAL_HINTS)
    is_evaluative_domain = bool(sig & EVAL_NEEDED_DOMAINS)

    if sig & RALPH_LOOP_HINTS or turns >= 100:
        mode = "Ralph Loop"
        reason = f"long-horizon hints in signature or median turns ≥ 100 (got {turns})"
    elif sig & PLAN_ACT_HINTS:
        mode = "Plan-then-Act"
        reason = f"signature contains planning verb(s): {sorted(sig & PLAN_ACT_HINTS)}"
    elif needs_eval:
        mode = "P/G/E (separate evaluator)"
        reason = f"signature contains review/eval verb(s): {sorted(sig & EVAL_HINTS)}"
    else:
        mode = "single-shot"
        reason = "short flow, no loop/plan/eval markers; one skill invocation is enough"

    warning = ""
    if is_evaluative_domain and not needs_eval and mode == "single-shot":
        warning = (
            "Harness 101 #03 warning: this skill produces an analytical/creative product "
            "(分析/解读/起草/...) but has no separate evaluator. Self-evaluating agents "
            "tend to over-declare victory. Consider splitting into Generator + Evaluator "
            "(two skill invocations) before promoting."
        )
    elif is_evaluative_domain and needs_eval and mode != "P/G/E (separate evaluator)":
        warning = (
            "Harness 101 #03 warning: signature mixes content production AND review "
            "verbs in one skill. Recommend P/G/E split — separate generator from evaluator."
        )

    return (mode, reason, warning)


# --- candidate scoring ---

def score(cluster: dict) -> int:
    return cluster["session_count"] * 2 + cluster["count"]


# --- watch.md accumulation ---

WATCH_HEADER = "# Workflow Packager — Watch List\n\n_Auto-accumulated across runs. When `hits >= min_occurrences`, items get promoted to candidates next run._\n\n| signature | hits | last_seen | sessions | sample |\n|-----------|------|-----------|----------|--------|\n"


def watch_load() -> dict[str, dict]:
    if not WATCH_FILE.exists():
        return {}
    rows: dict[str, dict] = {}
    for line in WATCH_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| signature") or line.startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        sig = cells[0]
        try:
            hits = int(cells[1])
            sessions = int(cells[3])
        except ValueError:
            continue
        rows[sig] = {
            "signature": sig,
            "hits": hits,
            "last_seen": cells[2],
            "sessions": sessions,
            "sample": cells[4],
        }
    return rows


def watch_write(rows: dict[str, dict]) -> None:
    lines = [WATCH_HEADER]
    sorted_rows = sorted(rows.values(), key=lambda r: -r["hits"])
    for r in sorted_rows:
        lines.append(f"| {r['signature']} | {r['hits']} | {r['last_seen']} | {r['sessions']} | {r['sample']} |")
    WATCH_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def signature_key(cluster: dict) -> str:
    return " / ".join(cluster.get("signature", []))


# --- main ---

def mine(days: int) -> dict:
    script = SKILL_DIR / "scripts" / "mine_patterns.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--days", str(days)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"mine_patterns failed: {proc.stderr}\n")
        sys.exit(proc.returncode)
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=30, help="window in days (default 30)")
    parser.add_argument("--min", type=int, default=3, help="min occurrences to be a candidate (default 3)")
    parser.add_argument("--watch-min", type=int, default=2, help="below this dropped entirely (default 2)")
    parser.add_argument("--overlap", type=float, default=0.7, help="Jaccard overlap with existing skill to skip (default 0.7)")
    parser.add_argument("--top", type=int, default=3, help="max candidates to surface (default 3)")
    parser.add_argument("--dry-run", action="store_true", help="print to stdout instead of writing file")
    args = parser.parse_args()

    mining = mine(args.days)
    clusters = mining["clusters"]
    existing = existing_skill_descriptions()

    candidates: list[dict] = []
    covered: list[dict] = []
    watch_new: list[dict] = []
    dropped_safety: list[dict] = []

    for c in clusters:
        sample_text = " ".join(c.get("samples", []))
        if has_secret(sample_text):
            dropped_safety.append({"reason": "secret/PII", "signature": signature_key(c)})
            continue
        if is_one_off(sample_text) and c["session_count"] < args.min:
            dropped_safety.append({"reason": "one-off marker", "signature": signature_key(c)})
            continue

        cluster_tokens = set(c.get("signature", []))
        best_overlap = (0.0, "")
        for name, desc_tokens in existing:
            j = jaccard(cluster_tokens, desc_tokens)
            if j > best_overlap[0]:
                best_overlap = (j, name)

        c["overlap"] = {"score": best_overlap[0], "with": best_overlap[1]}
        if best_overlap[0] >= args.overlap:
            covered.append(c)
            continue

        if c["session_count"] >= args.min:
            shape, reason = recommend_shape(c)
            c["shape"] = shape
            c["shape_reason"] = reason
            sched_mode, sched_reason, sched_warning = recommend_scheduling(c)
            c["scheduling_hint"] = sched_mode
            c["scheduling_reason"] = sched_reason
            if sched_warning:
                c["self_eval_warning"] = sched_warning
            c["score"] = score(c)
            ouro_why = is_ouro_candidate(sample_text)
            if ouro_why:
                c["route_hint"] = f"ouro (CogniVore): {ouro_why}"
            candidates.append(c)
        elif c["session_count"] >= args.watch_min:
            watch_new.append(c)

    candidates.sort(key=lambda c: -c["score"])

    today = dt.date.today().isoformat()
    report = _format_report(today, args, candidates[:args.top], candidates[args.top:], covered, watch_new, dropped_safety, mining)

    if args.dry_run:
        print(report)
        return 0

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out = CANDIDATES_DIR / f"{today}.md"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")

    # accumulate watch list
    existing_watch = watch_load()
    for c in watch_new + candidates[args.top:]:
        key = signature_key(c)
        if key in existing_watch:
            existing_watch[key]["hits"] += c["session_count"]
            existing_watch[key]["last_seen"] = today
            existing_watch[key]["sessions"] = max(existing_watch[key]["sessions"], c["session_count"])
        else:
            existing_watch[key] = {
                "signature": key,
                "hits": c["session_count"],
                "last_seen": today,
                "sessions": c["session_count"],
                "sample": redact((c.get("samples") or [""])[0][:60]).replace("\n", " "),
            }
    watch_write(existing_watch)
    print(f"updated {WATCH_FILE}")
    return 0


def _format_report(today, args, top, extras, covered, watch_new, dropped, mining) -> str:
    lines = [
        f"# Workflow Packager — Candidates ({today})\n",
        f"- scanned files: {mining['scanned_files']}",
        f"- total queries: {mining['total_queries']}",
        f"- clusters: {mining['cluster_count']}",
        f"- thresholds: days={args.days}  min={args.min}  watch-min={args.watch_min}  overlap={args.overlap}\n",
    ]

    lines.append("## Top Candidates\n")
    if not top:
        lines.append("_(no candidates met the threshold this run)_\n")
    else:
        lines.append("| # | signature | sessions | count | shape | scheduling | reason |")
        lines.append("|---|-----------|----------|-------|-------|------------|--------|")
        for i, c in enumerate(top, 1):
            sig = " / ".join(c["signature"])
            lines.append(
                f"| {i} | {sig} | {c['session_count']} | {c['count']} | "
                f"{c['shape']} | {c.get('scheduling_hint', '?')} | {c['shape_reason']} |"
            )
        lines.append("")
        lines.append("### Detail per candidate\n")
        for i, c in enumerate(top, 1):
            lines.append(f"#### Candidate {i} — `{' / '.join(c['signature'])}`")
            lines.append(f"- sessions: {c['session_count']}, total queries: {c['count']}")
            lines.append(f"- median session turns: {c['turn_count_median']}")
            lines.append(f"- tools observed: {c['tool_traces']}")
            lines.append(f"- shape: **{c['shape']}** — {c['shape_reason']}")
            lines.append(
                f"- scheduling: **{c.get('scheduling_hint', '?')}** — {c.get('scheduling_reason', '')}"
            )
            if c.get("self_eval_warning"):
                lines.append(f"- **!! self-eval warning**: {c['self_eval_warning']}")
            if c.get("route_hint"):
                lines.append(f"- **route hint**: 考虑改走 `{c['route_hint']}` — 看起来更像“吸收外部知识”而非“自下而上的工作流”")
            lines.append(f"- max overlap with existing skill: {c['overlap']['score']:.2f} ({c['overlap']['with']})")
            lines.append("- samples:")
            for s in c["samples"]:
                lines.append(f"  - {redact(s)[:100]}")
            lines.append("")

    if extras:
        lines.append("## Above min, but exceeded top-N cap (queued into watch)\n")
        for c in extras:
            lines.append(f"- `{' / '.join(c['signature'])}` (sessions={c['session_count']}, count={c['count']})")
        lines.append("")

    if covered:
        lines.append("## Already covered by existing skill (skipped)\n")
        for c in covered:
            lines.append(f"- `{' / '.join(c['signature'])}` ~ `{c['overlap']['with']}` (overlap={c['overlap']['score']:.2f})")
        lines.append("")

    if dropped:
        lines.append("## Dropped (safety / one-off)\n")
        for d in dropped:
            lines.append(f"- [{d['reason']}] `{d['signature']}`")
        lines.append("")

    lines.append("## Next steps (Phase 4)\n")
    lines.append("1. Read top candidates above; pick **≤ 3** to act on (the rest auto-go to watch.md).")
    lines.append("2. For each chosen candidate, draft an SKILL.md / shell-script / subagent doc per `references/packager-doctrine.md`.")
    lines.append("3. For Skills: place under `self/skills/<name>/` and run `./skillctl install`.")
    lines.append("4. Record what was created / skipped / watched below.\n")
    lines.append("## Decision Log\n")
    lines.append("_(append-only; populate during Phase 4)_\n")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
