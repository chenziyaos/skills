"""Observability helpers for the Ouro shadow runtime."""
from __future__ import annotations

from typing import Any

from .host_bridge import HostBridgeSnapshot
from .models import DecisionResult, PriorEvidenceSummary


def build_probe_observability(host_bridge: HostBridgeSnapshot) -> dict[str, Any]:
    """Describe probe feasibility without implying execution happened."""
    if host_bridge.capability_available("host.exec"):
        return {
            "mode": "available-but-not-executed",
            "dryRun": {
                "status": "not-executed",
                "reason": "Shadow runtime reports probe feasibility but does not execute dry-runs.",
            },
            "adversarial": {
                "status": "not-executed",
                "reason": "Shadow runtime reports adversarial feasibility but does not execute adversarial runs.",
            },
            "notes": "Sandbox capability exists, but this phase only emits advisory probe intent.",
        }
    return {
        "mode": "report-only",
        "dryRun": {
            "status": "skipped",
            "reason": "host.exec sandbox is unavailable, so probe steps stay report-only.",
        },
        "adversarial": {
            "status": "skipped",
            "reason": "host.exec sandbox is unavailable, so adversarial checks stay report-only.",
        },
        "notes": "No executable probe surface exists in this host snapshot.",
    }


def calibration_messages(
    host_bridge: HostBridgeSnapshot,
    decision_result: DecisionResult,
    governance_review: dict[str, Any],
    prior_summary: PriorEvidenceSummary,
) -> tuple[list[str], str | None]:
    """Produce degradation notes and a confidence cap."""
    degradations: list[str] = []
    confidence_cap: str | None = None
    if host_bridge.retrieval_mode == "memory-read-bm25":
        degradations.append("retrieval_mode=memory-read-bm25; semantic memory search is unavailable, so retrieval falls back to keyword-ranked ledger reads.")
    elif host_bridge.retrieval_mode == "context-only":
        degradations.append("retrieval_mode=context-only; semantic memory search and ledger reads are unavailable.")
        confidence_cap = "M" if host_bridge.ledger_size_bucket == "21+" else None
    if host_bridge.retrieval_mode == "memory-read-bm25" and not prior_summary.present:
        degradations.append("ledger_prior=no-match; retrieval is available but returned no prior decisions.")
    if prior_summary.unresolved_count > 0:
        degradations.append("ledger_prior=unresolved-history; prior outcomes remain pending or unresolved, so confidence stays capped.")
        confidence_cap = "M"
    if not host_bridge.capability_available("host.list_capabilities"):
        degradations.append("discovery_mode=passive; host.list_capabilities is unavailable.")
    if not host_bridge.capability_available("host.exec"):
        degradations.append("probe_mode=report-only; host.exec sandbox is unavailable.")
    if decision_result.boundary_ambiguity and decision_result.boundary_detail:
        degradations.append(f"decision_boundary={decision_result.boundary_detail}; evidence stays close to a neighboring route.")
        confidence_cap = "M"
    if governance_review.get("signal") and not governance_review.get("inventoryEvidencePresent"):
        degradations.append("governance signal is prompt-only; inventory evidence is absent.")
    return degradations, confidence_cap


def calibrate_confidence(decision: str | None, degradations: list[str], confidence_cap: str | None) -> str | None:
    """Calibrate H/M/L confidence from decision quality and degradations."""
    if decision is None:
        return None

    penalty = len(degradations)
    if confidence_cap == "M" and penalty == 0:
        penalty = 1

    if penalty == 0:
        return "H"
    if penalty == 1:
        return "M"
    return "L"
