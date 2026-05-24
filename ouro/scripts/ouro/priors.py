"""Read-only ledger prior summarization for the Ouro shadow runtime."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .models import PriorEvidenceSummary

UNRESOLVED_OUTCOMES = {"pending", "unresolved"}


def summarize_ledger_priors(records: tuple[dict[str, Any], ...]) -> PriorEvidenceSummary:
    """Summarize read-only ledger priors without implying lifecycle facts."""
    decision_counts = Counter(
        str(record["decision"])
        for record in records
        if record.get("decision") not in (None, "")
    )
    outcome_counts = Counter(
        str(record["outcome"])
        for record in records
        if record.get("outcome") not in (None, "")
    )
    unresolved_count = sum(
        1
        for outcome, count in outcome_counts.items()
        if outcome.lower() in UNRESOLVED_OUTCOMES
        for _ in range(count)
    )
    return PriorEvidenceSummary(
        present=bool(records),
        count=len(records),
        unresolved_count=unresolved_count,
        decision_counts=dict(sorted(decision_counts.items())),
        outcome_counts=dict(sorted(outcome_counts.items())),
        notes="Read-only ledger priors inform advisory confidence only; they do not assert lifecycle state.",
    )
