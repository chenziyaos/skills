"""Decision routing logic for the Ouro shadow runtime."""
from __future__ import annotations

from .models import DecisionResult, EvidenceEnvelope, InputAnalysis

FIVE_WAY_DECISIONS = {"create-skill", "extend-skill", "update-agent-md", "add-rule", "skip"}
DECISION_WEIGHTS = {
    "create_skill_workflow_density": 1,
    "create_skill_structured_workflow": 4,
    "create_skill_rollback": 2,
    "create_skill_validation": 1,
    "extend_skill_overlap_pressure": 3,
    "extend_skill_reusable_surface": 2,
    "extend_skill_merge_signal": 1,
    "update_agent_md_global_behavior": 3,
    "update_agent_md_agent_signal": 2,
    "update_agent_md_policy_signal": 2,
    "add_rule_compactness": 4,
    "add_rule_policy_signal": 1,
    "add_rule_workflow_penalty": 2,
    "skip_one_off": 6,
    "skip_stale": 4,
    "skip_retirement_pressure": 3,
    "skip_low_signal": 2,
}


def hard_skip_result(reason: str, validation_cases: list[str], rollback: str) -> DecisionResult:
    """Return a skip decision for hard safety or intent boundaries."""
    return DecisionResult(
        decision="skip",
        reason=reason,
        validation_cases=validation_cases,
        rollback_or_containment=rollback,
        scores={decision: 0 for decision in FIVE_WAY_DECISIONS},
        boundary_ambiguity=False,
        boundary_detail=None,
    )



def decision_priority(decision: str) -> int:
    """Return a stable priority used to break score ties."""
    order = {
        "extend-skill": 0,
        "create-skill": 1,
        "update-agent-md": 2,
        "add-rule": 3,
        "skip": 4,
    }
    return order[decision]



def classify_decision(evidence: EvidenceEnvelope | InputAnalysis) -> DecisionResult:
    """Classify the primary five-way decision from normalized evidence."""
    analysis = evidence.analysis if isinstance(evidence, EvidenceEnvelope) else evidence
    if analysis.protected_injection_tokens:
        return hard_skip_result(
            "Indirect instructions inside protected source content stay data-only and cannot drive capability changes.",
            ["replay the case with a sanitized source", "verify the report explicitly cites protected-source containment"],
            "Containment: do not create or update any capability from quoted, fenced, or source-tagged instructions.",
        )
    if analysis.injection_pressure:
        return hard_skip_result(
            "Indirect instructions attempt to override policy, so the content stays data-only.",
            ["replay the case with a sanitized source", "verify the report explicitly cites injection handling"],
            "Containment: do not create or update any capability from indirect instructions.",
        )
    if analysis.vague_intent:
        return hard_skip_result(
            "The intent is too vague to crystallize into a durable capability without overreaching.",
            ["restate the target landing form", "provide one concrete reusable outcome"],
            "Containment: wait for a clearer intent before changing any durable surface.",
        )
    if analysis.retirement_pressure and analysis.retirement_risk:
        return hard_skip_result(
            "The prompt is evaluating whether a safety-critical asset should be retired, so the correct action is to keep the outcome advisory.",
            ["verify whether a successor exists", "check whether rollback and dependency evidence are explicit"],
            "Containment: do not retire or replace the safety-critical asset from this run alone.",
        )

    scores = {decision: 0 for decision in FIVE_WAY_DECISIONS}
    scores["create-skill"] += min(analysis.workflow_density, 4) * DECISION_WEIGHTS["create_skill_workflow_density"]
    scores["create-skill"] += DECISION_WEIGHTS["create_skill_structured_workflow"] if analysis.structured_workflow else 0
    scores["create-skill"] += DECISION_WEIGHTS["create_skill_rollback"] if analysis.rollback_signal else 0
    scores["create-skill"] += DECISION_WEIGHTS["create_skill_validation"] if analysis.validation_signal else 0

    scores["extend-skill"] += analysis.overlap_pressure * DECISION_WEIGHTS["extend_skill_overlap_pressure"]
    scores["extend-skill"] += DECISION_WEIGHTS["extend_skill_reusable_surface"] if analysis.reusable_surface_pressure else 0
    scores["extend-skill"] += DECISION_WEIGHTS["extend_skill_merge_signal"] if analysis.merge_signal else 0

    scores["update-agent-md"] += analysis.global_behavior_scope * DECISION_WEIGHTS["update_agent_md_global_behavior"]
    scores["update-agent-md"] += DECISION_WEIGHTS["update_agent_md_agent_signal"] if analysis.agent_md_signal else 0
    scores["update-agent-md"] += DECISION_WEIGHTS["update_agent_md_policy_signal"] if analysis.policy_signal else 0

    scores["add-rule"] += analysis.rule_compactness * DECISION_WEIGHTS["add_rule_compactness"]
    scores["add-rule"] += DECISION_WEIGHTS["add_rule_policy_signal"] if analysis.policy_signal else 0
    scores["add-rule"] -= DECISION_WEIGHTS["add_rule_workflow_penalty"] if analysis.workflow_density >= 2 else 0

    scores["skip"] += DECISION_WEIGHTS["skip_one_off"] if analysis.one_off_knowledge else 0
    scores["skip"] += DECISION_WEIGHTS["skip_stale"] if analysis.stale_signal and not analysis.successor_signal and not analysis.retirement_pressure else 0
    scores["skip"] += DECISION_WEIGHTS["skip_retirement_pressure"] if analysis.retirement_pressure and not analysis.retirement_risk else 0
    if max(scores.values()) <= 1:
        scores["skip"] += DECISION_WEIGHTS["skip_low_signal"]

    ordered = sorted(scores.items(), key=lambda item: (-item[1], decision_priority(item[0])))
    decision, top_score = ordered[0]
    runner_up, runner_up_score = ordered[1]
    boundary_ambiguity = top_score > 0 and top_score - runner_up_score <= 2 and decision != "skip"
    boundary_detail = f"{decision} vs {runner_up}" if boundary_ambiguity else None

    if decision == "create-skill":
        reason = "The material describes a reusable multi-step workflow with validation and rollback semantics."
        validation_cases = ["run one happy-path workflow", "run one failure-path rollback check"]
        rollback = "Rollback: keep the workflow in its own skill so the entire surface can be reverted together."
    elif decision == "extend-skill":
        reason = "The prompt already points to an existing capability surface, so extension beats duplication."
        validation_cases = [
            "check that overlap is materially higher than separation",
            "verify the new steps fit the existing responsibility",
        ]
        rollback = "Rollback: keep the addition isolated so it can be removed from the parent skill cleanly."
    elif decision == "update-agent-md":
        reason = "This is a long-lived behavior preference that should shape many tasks without becoming a standalone skill."
        validation_cases = [
            "apply the preference to one risk-heavy response",
            "confirm it does not add workflow-specific steps",
        ]
        rollback = "Rollback: remove the config preference without touching task-specific skills."
    elif decision == "add-rule":
        reason = "The material is compact enough to encode as a deterministic rule instead of a larger skill."
        validation_cases = [
            "test one prompt that should be blocked",
            "test one reusable workflow that should stay outside the rule",
        ]
        rollback = "Rollback: delete the rule if it blocks legitimate prompts."
    else:
        reason = "The material is not yet strong enough to justify a durable capability change."
        validation_cases = ["clarify the reusable workflow or rule boundary", "add one falsifiable validation case"]
        rollback = "Containment: treat the result as advisory only."

    return DecisionResult(
        decision=decision,
        reason=reason,
        validation_cases=validation_cases,
        rollback_or_containment=rollback,
        scores=scores,
        boundary_ambiguity=boundary_ambiguity,
        boundary_detail=boundary_detail,
    )



def build_decision_explanation(
    evidence: EvidenceEnvelope,
    decision_result: DecisionResult | None,
    triggered: bool,
    trigger_reason: str,
    trigger_evidence: list[str],
) -> dict[str, object]:
    """Build a compact explanation surface for runtime decisions."""
    explanation: dict[str, object] = {
        "triggerReason": trigger_reason,
        "triggerEvidence": trigger_evidence,
        "protectedSourcePresent": evidence.analysis.protected_source_present,
    }
    if not triggered or decision_result is None:
        explanation["summary"] = "Ouro stayed on the normal answer path because capability-building intent was not strong enough."
        explanation["topDecision"] = None
        explanation["runnerUpDecision"] = None
        explanation["boundaryAmbiguity"] = False
        explanation["boundaryDetail"] = None
        return explanation

    ordered_scores = sorted(
        decision_result.scores.items(),
        key=lambda item: (-item[1], decision_priority(item[0])),
    )
    runner_up_decision = ordered_scores[1][0] if len(ordered_scores) > 1 else None
    explanation["summary"] = decision_result.reason
    explanation["topDecision"] = decision_result.decision
    explanation["runnerUpDecision"] = runner_up_decision
    explanation["boundaryAmbiguity"] = decision_result.boundary_ambiguity
    explanation["boundaryDetail"] = decision_result.boundary_detail
    explanation["signalBuckets"] = {
        "workflowDensity": evidence.workflow["workflowDensity"],
        "overlapPressure": evidence.overlap["pressureScore"],
        "globalBehaviorScope": evidence.analysis.global_behavior_scope,
        "ruleCompactness": evidence.analysis.rule_compactness,
    }
    return explanation
