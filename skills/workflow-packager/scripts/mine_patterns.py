#!/usr/bin/env python3
"""mine_patterns.py — mine local transcripts for repeated workflow patterns.

Pipeline:
  1. Discover transcript files (Cursor / Claude / Codex, best-effort)
  2. Extract user queries (initial + follow-ups) per session, normalize
  3. Tokenize (Chinese + English aware), score salient tokens per query
  4. Cluster queries by token Jaccard ≥ 0.5 (union-find)
  5. For each cluster: signature, count, session spread, samples, tool traces
  6. Emit JSON

No LLM, no network. See ../references/signal-patterns.md for design rationale.
"""

from __future__ import annotations

import argparse
import collections
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


# --- transcript discovery (mirrors skill-refiner; intentionally duplicated to keep skills portable) ---

def cursor_transcripts() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(
        str(HOME / ".cursor" / "projects" / "*" / "agent-transcripts" / "*" / "*.jsonl")
    ))


def claude_transcripts() -> list[Path]:
    root = HOME / ".claude" / "projects"
    return sorted(root.rglob("*.jsonl")) if root.is_dir() else []


def codex_transcripts() -> list[Path]:
    out: list[Path] = []
    for sub in ("log", "logs", "history", "chats"):
        root = HOME / ".codex" / sub
        if root.is_dir():
            out.extend(root.rglob("*.json"))
            out.extend(root.rglob("*.jsonl"))
    return sorted(out)


def within_days(path: Path, days: int | None) -> bool:
    if days is None:
        return True
    try:
        return (time.time() - path.stat().st_mtime) <= days * 86400
    except OSError:
        return False


# --- turn extraction ---

USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
TIMESTAMP_RE = re.compile(r"<timestamp>.*?</timestamp>", re.S)
SYSTEM_TAG_RE = re.compile(r"<system_reminder>.*?</system_reminder>|<attached_files>.*?</attached_files>", re.S)


SYSTEM_NOISE_PATTERNS = [
    # Cursor / CLI wrappers
    re.compile(r"<local-command-caveat>", re.I),
    re.compile(r"<command-name>", re.I),
    re.compile(r"<bash-input>", re.I),
    re.compile(r"<bash-stdout>", re.I),
    re.compile(r"<bash-stderr>", re.I),
    re.compile(r"<task-notification>", re.I),
    re.compile(r"<local-command-stdout>", re.I),
    re.compile(r"<tool-use-id>", re.I),
    # Conversational control / system status messages
    re.compile(r"^caveat: the messages below were generated", re.I),
    re.compile(r"^continue from where you left off", re.I),
    re.compile(r"^your previous response was interrupted", re.I),
    re.compile(r"^\[request interrupted by user", re.I),
    re.compile(r"^a session-scoped stop hook", re.I),
    re.compile(r"^goal set:", re.I),
    re.compile(r"^compacted \(", re.I),
    # ANSI escape (e.g. from cursor 'compacted' notice)
    re.compile(r"\x1b\["),
    # Implement-the-plan / standard plan-runner wrapper
    re.compile(r"# 目标\s*\n\s*Implement the plan as specified", re.I),
    re.compile(r"^Implement the plan as specified", re.I),
    # Git web UI canned text
    re.compile(r"^If the conflicts are too complex to resolve in the web editor", re.I),
    re.compile(r"^Check out, review, and resolve locally", re.I),
    # Test / "say X" smoke tests
    re.compile(r"^\s*say\s+(hello|hi)\b", re.I),
]

# Conversation control phrases — meta talk, not real workflow signal.
CONTROL_PHRASES = {
    # english
    "ok", "okay", "yes", "no", "go", "continue", "continue.", "next", "done", "next step",
    "exit", "exit 0", "pwd", "ls", "cd", "say hi", "say hello",
    # chinese
    "继续", "好的", "好", "嗯", "可以", "对", "是的", "不", "停", "停下", "结束",
    "下一步", "下一步计划", "继续吧", "继续测试", "测试通过",
}
CONTROL_PHRASES_LOWER = {p.lower() for p in CONTROL_PHRASES}

MIN_CONTENT_CHARS = 8
MIN_CONTENT_TOKENS = 3


def _is_real_query(text: str) -> bool:
    if not text or len(text) < MIN_CONTENT_CHARS:
        return False
    for pat in SYSTEM_NOISE_PATTERNS:
        if pat.search(text):
            return False
    stripped = text.strip().lower()
    if stripped in CONTROL_PHRASES_LOWER:
        return False
    # Reject if first line alone is a control phrase and message is short
    first_line = stripped.split("\n", 1)[0].strip().rstrip(".!?")
    if first_line in CONTROL_PHRASES_LOWER and len(stripped) < 30:
        return False
    return True


def _turn_text_user_only(blob: dict) -> str | None:
    """Return the human-authored text of a user turn, or None.

    Skips tool_result blocks (those are not user input).
    Strips <user_query>, <timestamp>, <system_*> wrappers.
    Filters control phrases and system-generated noise.
    """
    role = blob.get("role") or (blob.get("message") or {}).get("role")
    if role != "user":
        return None
    msg = blob.get("message") or blob
    content = msg.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
    text = "\n".join(parts)
    m = USER_QUERY_RE.search(text)
    if m:
        text = m.group(1)
    text = TIMESTAMP_RE.sub("", text)
    text = SYSTEM_TAG_RE.sub("", text)
    text = text.strip()
    if not _is_real_query(text):
        return None
    return text


def _turn_tools(blob: dict) -> list[str]:
    """Return list of tool names used in this turn (assistant role only)."""
    role = blob.get("role") or (blob.get("message") or {}).get("role")
    if role != "assistant":
        return []
    msg = blob.get("message") or blob
    content = msg.get("content")
    if not isinstance(content, list):
        return []
    return [
        block.get("name", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]


@dataclass
class SessionQueries:
    file: Path
    mtime: float
    queries: list[str]
    tool_uses: collections.Counter
    turn_count: int


def load_session(file: Path, max_queries: int) -> SessionQueries | None:
    queries: list[str] = []
    tool_uses: collections.Counter[str] = collections.Counter()
    turn_count = 0
    try:
        with file.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    blob = json.loads(line)
                except json.JSONDecodeError:
                    continue
                turn_count += 1
                ut = _turn_text_user_only(blob)
                if ut is not None and 0 < len(ut) < 500:
                    if len(queries) < max_queries:
                        queries.append(ut)
                for tool in _turn_tools(blob):
                    if tool:
                        tool_uses[tool] += 1
    except OSError:
        return None
    if not queries:
        return None
    try:
        mtime = file.stat().st_mtime
    except OSError:
        mtime = 0.0
    return SessionQueries(file=file, mtime=mtime, queries=queries, tool_uses=tool_uses, turn_count=turn_count)


# --- normalization + tokenization ---

STOPWORDS = {
    # english
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on", "at", "by", "with",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those",
    "can", "could", "should", "would", "will", "may", "might", "must",
    "from", "into", "about", "as", "if", "then", "than", "so", "not", "no", "yes",
    "please", "help", "me", "my", "your", "our",
    # chinese (high-frequency low-signal)
    "我们", "你们", "他们", "现在", "需要", "可以", "应该", "已经", "什么", "怎么", "为什么",
    "如何", "这个", "那个", "这些", "那些", "下面", "上面", "里面", "外面", "时候", "地方",
    "哪个", "哪里", "一下", "一些", "一点", "一个", "一种", "请帮", "帮我", "给我", "麻烦",
}

EN_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")
ZH_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
# LLM-must verbs (used to flip heuristic away from Shell-Automation)
LLM_VERBS = {
    "分析", "解读", "review", "评估", "建议", "总结", "起草", "理解", "解释",
    "writeup", "explain", "summarize", "analyze", "critique",
}
# Trigger words that suggest Subagent shape
SUBAGENT_HINTS = {"batch", "parallel", "并行", "批量", "多份", "并发", "all at once"}
# Tools that imply deterministic flow
DET_TOOLS = {"Shell", "Read", "Write", "Edit", "Glob", "Grep", "MultiEdit"}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\s\u3000]+", " ", text)
    return text.strip()


def tokens(text: str) -> list[str]:
    norm = normalize(text)
    raw = EN_TOKEN_RE.findall(norm) + ZH_TOKEN_RE.findall(norm)
    return [t for t in raw if t not in STOPWORDS and len(t) >= 2]


def salient_signature(toks: list[str], top: int = 5) -> tuple[str, ...]:
    if not toks:
        return ()
    counts = collections.Counter(toks)
    return tuple(t for t, _ in counts.most_common(top))


# --- clustering ---

@dataclass
class Query:
    text: str
    file: str
    mtime: float
    tokens: set[str]
    signature: tuple[str, ...]


class UnionFind:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def cluster(queries: list[Query], jaccard_min: float) -> list[list[int]]:
    n = len(queries)
    uf = UnionFind(n)
    # Bucket by token: only compare queries that share at least one token (sparse, O(N)-ish in practice).
    token_to_idxs: dict[str, list[int]] = collections.defaultdict(list)
    for i, q in enumerate(queries):
        for t in q.tokens:
            token_to_idxs[t].append(i)
    # For each token, pairwise within bucket (cap bucket size to avoid O(N^2) explosion on common words).
    BUCKET_CAP = 200
    for token, idxs in token_to_idxs.items():
        if len(idxs) > BUCKET_CAP:
            continue
        for i in range(len(idxs)):
            ti = queries[idxs[i]].tokens
            for j in range(i + 1, len(idxs)):
                tj = queries[idxs[j]].tokens
                if not ti or not tj:
                    continue
                inter = len(ti & tj)
                union_size = len(ti | tj)
                if union_size == 0:
                    continue
                if inter / union_size >= jaccard_min:
                    uf.union(idxs[i], idxs[j])
    groups: dict[int, list[int]] = collections.defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    return list(groups.values())


# --- main ---

def mine(days: int | None, jaccard_min: float, max_queries_per_session: int, sources: list[str]) -> dict:
    files: list[Path] = []
    if "cursor" in sources:
        files.extend(cursor_transcripts())
    if "claude" in sources:
        files.extend(claude_transcripts())
    if "codex" in sources:
        files.extend(codex_transcripts())
    files = [f for f in files if within_days(f, days)]

    queries: list[Query] = []
    file_to_session: dict[str, SessionQueries] = {}
    for f in files:
        sess = load_session(f, max_queries_per_session)
        if sess is None:
            continue
        file_to_session[str(f)] = sess
        for q in sess.queries:
            toks = tokens(q)
            unique = set(toks)
            if len(unique) < MIN_CONTENT_TOKENS:
                continue
            queries.append(Query(
                text=q,
                file=str(f),
                mtime=sess.mtime,
                tokens=unique,
                signature=salient_signature(toks),
            ))

    groups = cluster(queries, jaccard_min)

    clusters_out: list[dict] = []
    for g in groups:
        if not g:
            continue
        cluster_queries = [queries[i] for i in g]
        # aggregate signature: token frequencies across cluster
        all_tokens: collections.Counter[str] = collections.Counter()
        for q in cluster_queries:
            all_tokens.update(q.tokens)
        signature = [t for t, _ in all_tokens.most_common(5)]
        sessions = {q.file for q in cluster_queries}
        # tool traces across this cluster's sessions
        tool_traces: collections.Counter[str] = collections.Counter()
        turn_counts: list[int] = []
        for s in sessions:
            sess = file_to_session.get(s)
            if sess:
                tool_traces.update(sess.tool_uses)
                turn_counts.append(sess.turn_count)
        mtimes = [q.mtime for q in cluster_queries if q.mtime]
        clusters_out.append({
            "signature": signature,
            "count": len(cluster_queries),
            "session_count": len(sessions),
            "samples": [q.text[:80] for q in cluster_queries[:3]],
            "tool_traces": [t for t, _ in tool_traces.most_common(5)],
            "tool_traces_full": dict(tool_traces),
            "turn_count_median": (sorted(turn_counts)[len(turn_counts) // 2] if turn_counts else 0),
            "first_seen": (min(mtimes) if mtimes else 0),
            "last_seen": (max(mtimes) if mtimes else 0),
        })

    clusters_out.sort(key=lambda c: (-c["session_count"], -c["count"]))

    return {
        "scanned_files": len(files),
        "total_queries": len(queries),
        "cluster_count": len(clusters_out),
        "clusters": clusters_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=30, help="window in days; 0 = all (default 30)")
    parser.add_argument("--jaccard", type=float, default=0.5, help="cluster Jaccard threshold (default 0.5)")
    parser.add_argument("--max-queries", type=int, default=50, help="max queries kept per session (default 50)")
    parser.add_argument("--sources", default="cursor,claude,codex", help="comma-separated subset of {cursor,claude,codex}")
    args = parser.parse_args()
    days: int | None = args.days if args.days > 0 else None
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    result = mine(days, args.jaccard, args.max_queries, sources)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
