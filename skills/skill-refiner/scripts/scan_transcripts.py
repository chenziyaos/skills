#!/usr/bin/env python3
"""scan_transcripts.py — mine local agent transcripts for friction signals.

Doctrine (Skill 101 #2): real conversation evidence > guessed prompts.
This script never edits anything; it only emits a JSON summary that the
``skill-refiner`` workflow consumes downstream.

Sources (best-effort, missing ones silently skipped):
  - Cursor:  ~/.cursor/projects/*/agent-transcripts/*/*.jsonl
  - Claude:  ~/.claude/projects/*/  (best-effort)
  - Codex:   ~/.codex/log/*.json    (best-effort)

Privacy:
  - snippets default-truncated to 200 chars
  - no network calls
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


HOME = Path(os.path.expanduser("~"))

# --- Friction signal patterns (see references/friction-signals.md) ---

TIER1_PATTERNS = [
    ("negation",       re.compile(r"(不对|不是这样|wrong|that'?s not right|incorrect)", re.I)),
    ("explicit_miss",  re.compile(r"(为什么.*没.*触发|should have used|forgot to use|怎么没.*用.*skill)", re.I)),
    ("cancel",         re.compile(r"(算了|停[一]?下|cancel|nevermind|never mind)", re.I)),
    ("revert",         re.compile(r"(回滚|撤回|revert|undo|rollback)", re.I)),
]

TIER2_PATTERNS = [
    ("user_correction", re.compile(r"(你应该|你需要|should (do|use|be)|please instead|改一下)", re.I)),
    ("reject_choice",   re.compile(r"(不要这个|don'?t use that|wrong choice|换一个)", re.I)),
]


@dataclass
class Turn:
    idx: int
    role: str
    text: str       # concatenated text content (tool args excluded for privacy)
    file: Path


@dataclass
class FrictionEvent:
    tier: int
    kind: str
    snippet: str
    turn_idx: int
    role: str


@dataclass
class SkillHit:
    skill: str
    file: str
    hit_turn_idx: int
    hit_snippet: str
    signals: list[FrictionEvent] = field(default_factory=list)


# --- Schema-agnostic turn extraction ---

def _turn_text(blob: dict) -> str:
    """Extract human-authored text only — tool_results / tool_use / errors excluded.

    Friction signal detection runs on user turns; including tool_result content
    pollutes the stream with agent-generated noise (e.g. `<tool_use_error>`).
    """
    msg = blob.get("message") or blob
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


# Long blocks are pasted code/specs/instructions, not friction signals.
USER_TEXT_MAX_CHARS = 500
# Strip user_query wrappers Cursor injects.
USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)


def _clean_user_text(text: str) -> str:
    m = USER_QUERY_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _iter_jsonl(path: Path) -> Iterable[dict]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def load_turns(file: Path) -> list[Turn]:
    out: list[Turn] = []
    for idx, blob in enumerate(_iter_jsonl(file)):
        role = blob.get("role", "")
        if not role:
            msg = blob.get("message") or {}
            role = msg.get("role", "")
        text = _turn_text(blob)
        if text:
            out.append(Turn(idx=idx, role=role, text=text, file=file))
    return out


# --- Discovery of transcript files ---

def cursor_transcripts() -> list[Path]:
    pattern = str(HOME / ".cursor" / "projects" / "*" / "agent-transcripts" / "*" / "*.jsonl")
    return sorted(Path(p) for p in glob.glob(pattern))


def claude_transcripts() -> list[Path]:
    candidates: list[Path] = []
    root = HOME / ".claude" / "projects"
    if root.is_dir():
        candidates.extend(root.rglob("*.jsonl"))
    return sorted(candidates)


def codex_transcripts() -> list[Path]:
    candidates: list[Path] = []
    for sub in ("log", "logs", "history", "chats"):
        root = HOME / ".codex" / sub
        if root.is_dir():
            candidates.extend(root.rglob("*.json"))
            candidates.extend(root.rglob("*.jsonl"))
    return sorted(candidates)


# --- Time filtering (best-effort: file mtime) ---

def within_days(path: Path, days: int | None) -> bool:
    if days is None:
        return True
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    return (time.time() - mtime) <= days * 86400


# --- Skill mention detection ---

def build_skill_patterns(skill_name: str) -> list[re.Pattern[str]]:
    """Match the skill name in a few common shapes."""
    variants = {skill_name, skill_name.replace("-", " "), skill_name.replace("_", " ")}
    return [re.compile(rf"(?<![a-z0-9-]){re.escape(v)}(?![a-z0-9-])", re.I) for v in variants]


def find_skill_hits(turns: list[Turn], patterns: list[re.Pattern[str]]) -> list[int]:
    """Return list positions (not Turn.idx) for indexing into ``turns``."""
    hits: list[int] = []
    for pos, turn in enumerate(turns):
        for pat in patterns:
            if pat.search(turn.text):
                hits.append(pos)
                break
    return hits


def collect_signals(turns: list[Turn], hit_pos: int, window: int, snippet_cap: int) -> list[FrictionEvent]:
    lo = max(0, hit_pos - window)
    hi = min(len(turns), hit_pos + window + 1)
    out: list[FrictionEvent] = []
    seen: set[tuple[int, str]] = set()  # (turn_idx, kind) dedupe per window
    for t in turns[lo:hi]:
        if t.role != "user":
            continue
        clean = _clean_user_text(t.text)
        if not clean or len(clean) > USER_TEXT_MAX_CHARS:
            # Long blocks are usually pasted code or instructions, not friction.
            continue
        for tier_no, patterns in ((1, TIER1_PATTERNS), (2, TIER2_PATTERNS)):
            for kind, pat in patterns:
                m = pat.search(clean)
                if not m:
                    continue
                if (t.idx, kind) in seen:
                    continue
                seen.add((t.idx, kind))
                out.append(FrictionEvent(
                    tier=tier_no, kind=kind, role=t.role,
                    snippet=_snippet(clean, m, snippet_cap), turn_idx=t.idx,
                ))
    return out


def _snippet(text: str, match: re.Match[str], cap: int) -> str:
    start = max(0, match.start() - 40)
    end = min(len(text), match.end() + 40)
    raw = text[start:end].replace("\n", " ").strip()
    if len(raw) > cap:
        raw = raw[: cap - 3] + "..."
    return raw


# --- Main scan ---

def scan(skill_name: str, days: int | None, window: int, snippet_cap: int, sources: list[str]) -> dict:
    files: list[Path] = []
    if "cursor" in sources:
        files.extend(cursor_transcripts())
    if "claude" in sources:
        files.extend(claude_transcripts())
    if "codex" in sources:
        files.extend(codex_transcripts())

    files = [f for f in files if within_days(f, days)]
    patterns = build_skill_patterns(skill_name)

    hits: list[SkillHit] = []
    for file in files:
        turns = load_turns(file)
        if not turns:
            continue
        skill_hits = find_skill_hits(turns, patterns)
        if not skill_hits:
            continue
        # collapse adjacent hits (same conversation cluster)
        seen_window = -10**9
        clusters: list[int] = []
        for h in skill_hits:
            if h - seen_window > window:
                clusters.append(h)
            seen_window = h
        for hit_pos in clusters:
            hit_turn = turns[hit_pos]
            signals = collect_signals(turns, hit_pos, window, snippet_cap)
            hits.append(SkillHit(
                skill=skill_name,
                file=str(file),
                hit_turn_idx=hit_turn.idx,
                hit_snippet=_first_line(hit_turn.text, snippet_cap),
                signals=signals,
            ))

    return {
        "skill": skill_name,
        "scanned_files": len(files),
        "hits": [
            {
                "file": h.file,
                "hit_turn_idx": h.hit_turn_idx,
                "hit_snippet": h.hit_snippet,
                "signals": [s.__dict__ for s in h.signals],
            }
            for h in hits
        ],
        "summary": {
            "hits_total": len(hits),
            "tier1_total": sum(1 for h in hits for s in h.signals if s.tier == 1),
            "tier2_total": sum(1 for h in hits for s in h.signals if s.tier == 2),
        },
    }


def _first_line(text: str, cap: int) -> str:
    line = text.strip().splitlines()[0] if text.strip() else ""
    if len(line) > cap:
        line = line[: cap - 3] + "..."
    return line


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="skill name to search for")
    parser.add_argument("--days", type=int, default=30, help="only scan files modified in last N days (default 30; 0=all)")
    parser.add_argument("--window", type=int, default=10, help="± N turns around each skill mention to scan for signals")
    parser.add_argument("--snippet-cap", type=int, default=200, help="max chars per snippet")
    parser.add_argument(
        "--sources",
        default="cursor,claude,codex",
        help="comma-separated subset of {cursor,claude,codex}",
    )
    args = parser.parse_args()

    days: int | None = args.days if args.days > 0 else None
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    result = scan(args.skill, days, args.window, args.snippet_cap, sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
