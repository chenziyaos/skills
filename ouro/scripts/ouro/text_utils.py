"""Shared text and asset helper utilities for the Ouro shadow runtime."""
from __future__ import annotations

import re
from typing import Any

PROTECTED_SEGMENT_PATTERNS = (
    re.compile(r"```.*?```", re.DOTALL),
    re.compile(
        r"<(?:source|quote|doc|context|citation|external|paste)\b[^>]*>.*?</(?:source|quote|doc|context|citation|external|paste)>",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"<(?:pre|code)\b[^>]*>.*?</(?:pre|code)>", re.IGNORECASE | re.DOTALL),
    re.compile(r"(?m)(?:^\t.*(?:\n|$))+"),
    re.compile(r"(?m)(?:^>.*(?:\n|$))+"),
    re.compile(r"“[^”]*”", re.DOTALL),
)
SENSITIVE_PREVIEW_PATTERNS = (
    (re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"), "<redacted-email>"),
    (re.compile(r"(?i)\b(?:sk|rk|pk|ghp)_[A-Za-z0-9_-]{16,}\b"), "<redacted-token>"),
    (re.compile(r"(?i)\bsk-ant-[A-Za-z0-9_-]{16,}\b"), "<redacted-token>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<redacted-token>"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "<redacted-token>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "<redacted-jwt>"),
    (
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----", re.DOTALL),
        "<redacted-private-key>",
    ),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{16,}\b"), "<redacted-bearer>"),
)
ASSET_ID_PATTERN = re.compile(r"`([^`]+)`")
ASSET_ID_CHAR_CLASS = r"[a-z0-9_-]"
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
LIST_ITEM_PATTERN = re.compile(r"^\s*-\s+", re.MULTILINE)


def contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    """Return whether any token appears in the text."""
    return any(token.lower() in text for token in tokens)


def has_explicit_ouro_invocation(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    """Return whether the prompt explicitly invokes Ouro instead of merely mentioning its name."""
    return any(pattern.search(text) for pattern in patterns)


def matched_tokens(text: str, tokens: tuple[str, ...]) -> tuple[str, ...]:
    """Return distinct tokens that appear in the text."""
    return tuple(token for token in tokens if token.lower() in text)


def merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping protected-content spans."""
    if not spans:
        return []
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def split_direct_and_protected_text(text: str) -> tuple[str, str]:
    """Split direct user instructions from protected source-like content."""
    spans: list[tuple[int, int]] = []
    for pattern in PROTECTED_SEGMENT_PATTERNS:
        spans.extend((match.start(), match.end()) for match in pattern.finditer(text))
    merged = merge_spans(spans)
    if not merged:
        return text, ""

    direct_parts: list[str] = []
    protected_parts: list[str] = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            direct_parts.append(text[cursor:start])
        protected_parts.append(text[start:end])
        cursor = end
    if cursor < len(text):
        direct_parts.append(text[cursor:])
    return "\n".join(part for part in direct_parts if part), "\n".join(protected_parts)


def redact_sensitive_preview(text: str) -> str:
    """Redact obvious secrets and identifiers before persisting prompt preview."""
    redacted = text
    for pattern, replacement in SENSITIVE_PREVIEW_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def infer_asset_ids(text: str, assets: list[dict[str, Any]]) -> list[str]:
    """Infer relevant asset ids from prompt text and optional inventory evidence."""
    lowered = text.lower()
    known_asset_ids = [str(asset.get("asset_id")) for asset in assets if asset.get("asset_id")]
    ids: list[str] = []
    for asset_id_text in known_asset_ids:
        pattern = re.compile(
            rf"(?<!{ASSET_ID_CHAR_CLASS}){re.escape(asset_id_text.lower())}(?!{ASSET_ID_CHAR_CLASS})"
        )
        if asset_id_text not in ids and pattern.search(lowered):
            ids.append(asset_id_text)
    for raw_item in ASSET_ID_PATTERN.findall(text):
        item = raw_item.strip()
        if not item or item in ids:
            continue
        normalized = item.lower()
        if item in known_asset_ids:
            ids.append(item)
            continue
        if "/" in item or "." in item or " " in item:
            continue
        if "-" in item and re.fullmatch(r"[A-Za-z0-9_-]+", item):
            ids.append(item)
            continue
        if re.fullmatch(r"[A-Za-z]+-v\d+", item):
            ids.append(item)
    return ids


def inventory_supports_assets(asset_ids: list[str], assets: list[dict[str, Any]]) -> bool:
    """Return whether the inventory supports any mentioned asset ids."""
    if not asset_ids or not assets:
        return False
    known = {str(asset.get("asset_id")) for asset in assets if asset.get("asset_id")}
    return any(asset_id in known for asset_id in asset_ids)


def merge_asset_evidence(*asset_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge inventory and host-observed assets without losing evidence provenance."""
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for asset_group in asset_groups:
        for item in asset_group:
            if not isinstance(item, dict):
                continue
            asset_id = item.get("asset_id")
            if not asset_id:
                continue
            key = str(asset_id)
            if key not in merged:
                merged[key] = {
                    "asset_id": key,
                    "asset_type": item.get("asset_type"),
                    "scope": item.get("scope"),
                    "successor_of": item.get("successor_of"),
                    "merged_into": item.get("merged_into"),
                    "depends_on": list(item.get("depends_on") or []),
                    "evidence_sources": list(item.get("evidence_sources") or []),
                }
                order.append(key)
                continue
            current = merged[key]
            for field in ("asset_type", "scope", "successor_of", "merged_into"):
                if current.get(field) in (None, "") and item.get(field) not in (None, ""):
                    current[field] = item.get(field)
            current_dependencies = current.setdefault("depends_on", [])
            for dependency in item.get("depends_on") or []:
                dependency_text = str(dependency)
                if dependency_text not in current_dependencies:
                    current_dependencies.append(dependency_text)
            current_sources = current.setdefault("evidence_sources", [])
            for source in item.get("evidence_sources") or []:
                source_text = str(source)
                if source_text not in current_sources:
                    current_sources.append(source_text)
    return [merged[asset_id] for asset_id in order]


def dedupe_strings(values: list[str]) -> list[str]:
    """Deduplicate strings while preserving order."""
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def safe_slug(value: str) -> str:
    """Return a filesystem-safe slug."""
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "-", value.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-._")
    return cleaned or "artifact"
