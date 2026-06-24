# Ouro — Governance-Aware Report Examples (Draft)

> Example reports showing how `governance_signal` can appear without breaking the current five-way primary decision contract.

## Example 1 — Extension with freeze pressure

```markdown
## CogniVore Report

**Input Type**: skill-increment
**Core Value**: adds durable review quality, but maintenance burden is rising
**Decision**: extend-skill
**Governance Signal**: freeze-candidate
**Evidence Maturity**: supported-signal
**Inventory Evidence Present**: false
**Evidence Basis**: overlap, impact-reasoning
**Confidence**: M
**Ledger ID**: <uuid>

### Mirror Scan
Existing skill already covers most of the behavior. Overlap is moderate rather than high enough to force merge, so extension is still the best routing decision.

### Governance Review
Signal: `freeze-candidate`
Reason: the capability still has clear benefit, but every host/runtime change now requires additional maintenance. Expand now, but treat further growth as likely uneconomic.
```

## Example 2 — Skip with retirement blocked

```markdown
## CogniVore Report

**Input Type**: rule-review
**Core Value**: protects high-risk operations by requiring rollback planning
**Decision**: skip
**Governance Signal**: retirement-blocked
**Evidence Maturity**: supported-signal
**Inventory Evidence Present**: false
**Evidence Basis**: successor-evidence, dependency-evidence, impact-reasoning
**Confidence**: L
**Ledger ID**: <uuid>

### Rewrite Plan
Recommended action: `skip`
Reason: the proposal is not to create or extend a new capability, but to remove a safety-critical rule without a proven replacement.

### Governance Review
Signal: `retirement-blocked`
Reason: removal is under-evidenced. No clear successor exists and rollback/safety consequences remain high.
```

## Example 3 — Update config with merge pressure

```markdown
## CogniVore Report

**Input Type**: behavior-policy
**Core Value**: standardizes high-risk response ordering
**Decision**: update-agent-md
**Governance Signal**: merge-candidate
**Evidence Maturity**: supported-signal
**Inventory Evidence Present**: true
**Evidence Basis**: overlap, successor-evidence, impact-reasoning
**Confidence**: M
**Ledger ID**: <uuid>

### Mirror Scan
A global config and an existing rule now express nearly the same risk-first behavior.

### Governance Review
Signal: `merge-candidate`
Reason: duplication is creating maintenance ambiguity. Given the inventory evidence, governance confidence is stronger than in a prompt-only case.
```
