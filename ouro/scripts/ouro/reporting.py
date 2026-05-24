"""Reporting helpers for the Ouro shadow runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EvidenceEnvelope, PriorEvidenceSummary
from .text_utils import redact_sensitive_preview


def shadow_boundary() -> dict[str, Any]:
    """Return the immutable shadow-runtime safety boundary."""
    return {
        "advisoryOnly": True,
        "writesLedger": False,
        "executesSelfDigest": False,
        "mutatesSkillSurface": False,
        "mutatesAgentConfig": False,
        "mutatesRules": False,
    }

def next_action(decision: str, governance_review: dict[str, Any]) -> str:
    """Return the next-action summary for the result."""
    if decision == "create-skill":
        return "Draft a standalone skill surface and keep the workflow isolated for rollback."
    if decision == "extend-skill":
        action = "Add the new behavior to the existing skill instead of creating a parallel asset."
        if governance_review.get("signal") == "merge-candidate":
            return f"{action} If needed, emit merge pressure only as a run-scoped semirun observation."
        return action
    if decision == "update-agent-md":
        return "Update the persistent agent behavior contract without inventing a new skill."
    if decision == "add-rule":
        return "Encode the behavior as one deterministic rule and verify the blocked case explicitly."
    return "Do not persist durable changes; keep the result as a run-scoped advisory observation until stronger evidence exists."


def build_result_payload(
    *,
    text: str,
    source_metadata: dict[str, Any],
    inventory_metadata: dict[str, Any] | None,
    retrieval: str,
    run_id: str,
    timestamp: str,
    input_hash: str,
    host_snapshot: dict[str, Any],
    triggered: bool,
    trigger_reason: str,
    trigger_evidence: list[str],
    evidence: EvidenceEnvelope,
    probe: dict[str, Any],
    decision: str | None,
    confidence: str | None,
    degradations: list[str],
    report: dict[str, Any],
    governance_review: dict[str, Any],
    prior_summary: PriorEvidenceSummary,
    control_plane: dict[str, Any],
    observability: dict[str, Any] | None,
    output_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the shared result payload for triggered and non-triggered runs."""
    return {
        "schemaVersion": 1,
        "mode": "shadow",
        "runId": run_id,
        "ts": timestamp,
        "input": {
            **source_metadata,
            "sha256_12": input_hash,
            "preview": redact_sensitive_preview(text[:200]),
            "assetInventoryFile": Path(inventory_metadata["path"]).name if inventory_metadata else None,
        },
        "host": host_snapshot,
        "trigger": {
            "triggered": triggered,
            "reason": trigger_reason,
            "evidence": trigger_evidence,
        },
        "decision": decision,
        "confidence": confidence,
        "retrievalMode": retrieval,
        "degradations": degradations,
        "priorEvidence": {
            "mode": retrieval,
            "readOnly": True,
            "ledgerPriorsPresent": prior_summary.present,
            "ledgerPriorCount": prior_summary.count,
            "unresolvedCount": prior_summary.unresolved_count,
            "decisionCounts": prior_summary.decision_counts,
            "outcomeCounts": prior_summary.outcome_counts,
            "notes": prior_summary.notes,
        },
        "evidence": {
            "trigger": evidence.trigger,
            "workflow": evidence.workflow,
            "overlap": evidence.overlap,
            "governance": evidence.governance,
        },
        "probe": probe,
        "controlPlane": control_plane,
        "shadowBoundary": shadow_boundary(),
        "report": report,
        "governanceReview": governance_review,
        "observability": observability,
        "outputPolicy": output_policy,
        "artifacts": {
            "runResultJson": None,
            "governanceReviewYaml": None,
        },
    }
