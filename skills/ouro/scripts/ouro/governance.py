"""Governance advisory logic for the Ouro shadow runtime."""
from __future__ import annotations

from .models import DecisionResult, EvidenceEnvelope
from .text_utils import dedupe_strings


NOTE_TEMPLATES = {
    "retirement-blocked": "The proposal looks like retirement pressure, but the safety envelope is incomplete; this remains an advisory observation only.",
    "deprecate-candidate": "A clearer successor relationship exists than continued parallel growth; this does not mean deprecation already happened.",
    "freeze-candidate": "Low recent usage does not justify retirement on its own; this is advisory governance pressure, not a lifecycle fact.",
    "merge-candidate": "Overlap pressure is high enough that governance should prefer merging surfaces over parallel expansion; this does not mean a merge already happened.",
}


def matched_assets(asset_ids: tuple[str, ...], assets: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return inventory assets that match mentioned ids."""
    known = {asset_id for asset_id in asset_ids}
    return [asset for asset in assets if str(asset.get("asset_id")) in known]



def build_governance_notes(signal: str, *, boundary_ambiguity: bool) -> str:
    """Build advisory governance notes without implying lifecycle facts."""
    notes = [NOTE_TEMPLATES[signal]]
    if signal == "merge-candidate" and boundary_ambiguity:
        notes.append("Primary routing remains close to a neighboring decision even though merge pressure is visible.")
    return " ".join(notes)


def infer_governance_review(
    evidence: EvidenceEnvelope,
    decision_result: DecisionResult,
    assets: list[dict[str, object]],
) -> dict[str, object]:
    """Infer advisory governance outputs without mutating lifecycle state."""
    analysis = evidence.analysis
    asset_id = analysis.asset_ids[0] if analysis.asset_ids else None
    relevant_assets = matched_assets(analysis.asset_ids, assets)
    dependency_evidence = any(asset.get("depends_on") for asset in relevant_assets)
    successor_inventory_evidence = any(asset.get("successor_of") or asset.get("merged_into") for asset in relevant_assets)
    successor_evidence = successor_inventory_evidence or (
        analysis.successor_signal and not analysis.stale_signal and not analysis.retirement_pressure
    )
    strong_overlap = analysis.overlap_pressure >= 2 or (analysis.merge_signal and analysis.reusable_surface_pressure)

    signal: str | None = None
    evidence_basis: list[str] = []
    impact_posture: str | None = None

    if analysis.retirement_pressure and (analysis.retirement_risk or dependency_evidence):
        signal = "retirement-blocked"
        evidence_basis.extend(["dependency-evidence", "impact-reasoning"])
        impact_posture = "worth-keeping"
    elif successor_evidence and not (analysis.retirement_pressure and analysis.retirement_risk):
        signal = "deprecate-candidate"
        evidence_basis.extend(["successor-evidence", "impact-reasoning"])
        impact_posture = "candidate-for-retirement"
    elif analysis.stale_signal:
        signal = "freeze-candidate"
        evidence_basis.append("impact-reasoning")
        impact_posture = "keep-but-freeze"
    elif strong_overlap:
        signal = "merge-candidate"
        evidence_basis.extend(["overlap", "impact-reasoning"])
        impact_posture = "candidate-for-merge"

    if dependency_evidence and signal == "retirement-blocked" and "dependency-evidence" not in evidence_basis:
        evidence_basis.append("dependency-evidence")
    has_attributed_asset_evidence = analysis.inventory_evidence_present or bool(relevant_assets)
    if signal and not has_attributed_asset_evidence and "attribution-uncertainty" not in evidence_basis:
        evidence_basis.append("attribution-uncertainty")
    evidence_basis = dedupe_strings(evidence_basis)
    evidence_maturity: str | None = None
    if signal:
        if analysis.inventory_evidence_present and "attribution-uncertainty" not in evidence_basis and len(evidence_basis) >= 2:
            evidence_maturity = "well-evidenced"
        elif len(evidence_basis) >= 2 and "attribution-uncertainty" not in evidence_basis:
            evidence_maturity = "supported-signal"
        else:
            evidence_maturity = "prompt-only"

    return {
        "assetId": asset_id,
        "signal": signal,
        "evidenceMaturity": evidence_maturity,
        "inventoryEvidencePresent": analysis.inventory_evidence_present,
        "evidenceBasis": evidence_basis,
        "impactPosture": impact_posture,
        "notes": build_governance_notes(signal, boundary_ambiguity=decision_result.boundary_ambiguity) if signal else None,
    }
