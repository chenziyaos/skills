"""Trigger detection helpers for the Ouro shadow runtime."""
from __future__ import annotations

from .models import EvidenceEnvelope


def detect_trigger(evidence: EvidenceEnvelope) -> tuple[bool, str, list[str]]:
    """Determine whether Ouro should trigger on the input."""
    analysis = evidence.analysis
    reasons: list[str] = []
    if analysis.explicit_trigger:
        reasons.append("explicit ouro invocation")
    if analysis.behavior_trigger_hits and analysis.capability_context_hits:
        reasons.append("capability-building ingestion intent")
    if analysis.semantic_false_positive:
        return False, "semantic false positive without capability-building intent", ["normal q&a path"]
    if analysis.raw_url_only:
        return False, "raw URL without capability intent", ["normal q&a path"]
    if reasons:
        return True, reasons[0], reasons
    return False, "no capability-building intent detected", ["normal q&a path"]
