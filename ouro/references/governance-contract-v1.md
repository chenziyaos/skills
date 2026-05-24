# Ouro — Governance Contract v1

> Minimal governance protocol contract for Ouro after introducing governance-aware reporting, but before Ledger schema integration.

## Contract intent

This contract formalizes governance reasoning as a **secondary advisory layer**.

It does **not**:
- replace the five-way primary decision taxonomy
- execute lifecycle transitions
- require immediate Ledger schema changes

## Core layering

### Primary decision
Answers: where should the input land now?

Allowed values:
- `create-skill`
- `extend-skill`
- `update-agent-md`
- `add-rule`
- `skip`

### Governance signal
Answers: what governance posture should be surfaced around that decision?

Allowed values:
- `merge-candidate`
- `freeze-candidate`
- `deprecate-candidate`
- `retirement-blocked`
- `null`

### Evidence envelope
Required whenever governance reasoning is surfaced:
- `evidence_maturity`: `design-intent | early-signal | well-evidenced`
- `inventory_evidence_present`: `true | false`
- `evidence_basis`: one or more of
  - `overlap`
  - `successor-evidence`
  - `dependency-evidence`
  - `impact-reasoning`
  - `attribution-uncertainty`

## Hard invariants

1. `Decision` remains the only routing output.
2. `Governance Signal` is advisory, not executable.
3. `Governance Signal` is not a lifecycle state.
4. Missing inventory / successor / dependency evidence forces candidate / blocked language only.
5. Low attribution confidence blocks strong value-expansion conclusions.
6. Repo-local Python shadow artifacts may record advisory observations, but they must not claim lifecycle facts or durable governance state.

## Report-level shape

```yaml
Decision: <five-way primary decision>
Governance Signal: <null | merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked>
Evidence Maturity: <design-intent | early-signal | well-evidenced>
Inventory Evidence Present: <true | false>
Evidence Basis: [<one or more short reasons>]
```

## Evaluation-level shape

Evaluation and runtime result templates should record at least:
- governance signal actual
- evidence maturity
- inventory evidence present
- impact posture / attribution posture where relevant

## Out of scope for v1

- direct Ledger core schema fields
- executable merge/deprecate/retire actions
- replacing the primary decision taxonomy
- lifecycle state mutation as report facts
