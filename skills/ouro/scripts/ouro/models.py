"""Shared runtime data models for the Ouro shadow runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InputAnalysis:
    """Normalized evidence extracted from the prompt."""

    explicit_trigger: bool
    protected_source_present: bool
    protected_trigger_names: tuple[str, ...]
    protected_injection_tokens: tuple[str, ...]
    behavior_trigger_tokens: tuple[str, ...]
    capability_context_tokens: tuple[str, ...]
    raw_url_present: bool
    raw_url_only: bool
    semantic_false_positive: bool
    workflow_tokens: tuple[str, ...]
    structured_workflow_tokens: tuple[str, ...]
    validation_tokens: tuple[str, ...]
    rollback_signal: bool
    overlap_tokens: tuple[str, ...]
    global_behavior_tokens: tuple[str, ...]
    rule_tokens: tuple[str, ...]
    policy_tokens: tuple[str, ...]
    agent_md_tokens: tuple[str, ...]
    one_off_knowledge: bool
    vague_intent: bool
    injection_pressure: bool
    retirement_pressure: bool
    retirement_risk: bool
    stale_signal: bool
    successor_signal: bool
    merge_signal: bool
    asset_ids: tuple[str, ...]
    inventory_evidence_present: bool
    bullet_count: int

    @property
    def behavior_trigger_hits(self) -> int:
        return len(self.behavior_trigger_tokens)

    @property
    def capability_context_hits(self) -> int:
        return len(self.capability_context_tokens)

    @property
    def workflow_density(self) -> int:
        density = len(self.workflow_tokens) + len(self.structured_workflow_tokens)
        if self.bullet_count >= 3:
            density += 1
        if self.validation_signal:
            density += 1
        return density

    @property
    def structured_workflow(self) -> bool:
        return len(self.structured_workflow_tokens) >= 2 or (len(self.workflow_tokens) >= 2 and self.rollback_signal)

    @property
    def validation_signal(self) -> bool:
        return bool(self.validation_tokens)

    @property
    def overlap_pressure(self) -> int:
        return len(self.overlap_tokens) + (1 if len(self.asset_ids) >= 2 else 0)

    @property
    def global_behavior_scope(self) -> int:
        return len(self.global_behavior_tokens) + len(self.agent_md_tokens)

    @property
    def rule_compactness(self) -> int:
        return len(self.rule_tokens)

    @property
    def policy_signal(self) -> bool:
        return bool(self.policy_tokens)

    @property
    def agent_md_signal(self) -> bool:
        return bool(self.agent_md_tokens)

    @property
    def reusable_surface_pressure(self) -> bool:
        return self.overlap_pressure > 0 or len(self.asset_ids) >= 1


@dataclass(frozen=True)
class EvidenceEnvelope:
    """Structured evidence shared by routing, governance, and reporting."""

    analysis: InputAnalysis
    trigger: dict[str, Any]
    workflow: dict[str, Any]
    overlap: dict[str, Any]
    governance: dict[str, Any]


@dataclass(frozen=True)
class DecisionResult:
    """Primary decision plus scoring metadata."""

    decision: str
    reason: str
    validation_cases: list[str]
    rollback_or_containment: str
    scores: dict[str, int]
    boundary_ambiguity: bool
    boundary_detail: str | None


@dataclass(frozen=True)
class PriorEvidenceSummary:
    """Read-only ledger prior summary used for advisory calibration."""

    present: bool
    count: int
    unresolved_count: int
    decision_counts: dict[str, int]
    outcome_counts: dict[str, int]
    notes: str
