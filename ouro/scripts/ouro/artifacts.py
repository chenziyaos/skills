"""Artifact emission helpers for the Ouro shadow runtime."""
from __future__ import annotations

from typing import Any

from .decision import FIVE_WAY_DECISIONS


def governance_artifact_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    """Build the companion semirun governance artifact payload when it is allowed."""
    review = result.get("governanceReview") or {}
    signal = review.get("signal")
    evidence_maturity = review.get("evidenceMaturity")
    evidence_basis = review.get("evidenceBasis") or []
    if signal is None:
        return None
    if result.get("decision") not in FIVE_WAY_DECISIONS:
        return None
    if not review.get("inventoryEvidencePresent"):
        return None
    if not evidence_maturity or not evidence_basis:
        return None
    asset_id = review.get("assetId") or "unknown-asset"
    return {
        "governance_review": {
            "asset_id": asset_id,
            "run_id": result["runId"],
            "ts": result["ts"],
            "primary_decision": result["decision"],
            "signal": signal,
            "evidence_maturity": evidence_maturity,
            "inventory_evidence_present": bool(review.get("inventoryEvidencePresent")),
            "evidence_basis": evidence_basis,
            "impact_posture": review.get("impactPosture"),
            "notes": review.get("notes"),
        }
    }


def dump_governance_yaml(payload: dict[str, Any]) -> str:
    """Serialize the companion governance artifact as YAML."""
    review = payload["governance_review"]
    lines = ["governance_review:"]
    for key in (
        "asset_id",
        "run_id",
        "ts",
        "primary_decision",
        "signal",
        "evidence_maturity",
        "inventory_evidence_present",
    ):
        lines.append(f"  {key}: {format_yaml_scalar(review.get(key))}")
    lines.append("  evidence_basis:")
    for item in review.get("evidence_basis") or []:
        lines.append(f"    - {item}")
    lines.append(f"  impact_posture: {format_yaml_scalar(review.get('impact_posture'))}")
    notes = review.get("notes")
    if notes:
        lines.append("  notes: |")
        for line in str(notes).splitlines():
            lines.append(f"    {line}")
    return "\n".join(lines) + "\n"


def format_yaml_scalar(value: Any) -> str:
    """Format a scalar for the small YAML subset we emit."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
