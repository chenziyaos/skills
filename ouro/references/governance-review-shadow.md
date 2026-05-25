# Ouro — Governance Review Shadow (Draft)

> Draft for a Ledger-adjacent, non-authoritative persistence shape for governance reasoning.

## Purpose

Governance signals should become persistable before they become first-class Ledger schema facts.

This shadow structure is intended to:
- preserve governance reasoning across runs
- support audit and comparison
- avoid polluting the core Ledger decision schema too early

## Recommended shape

```yaml
governance_review:
  asset_id: <stable asset identifier>
  run_id: <run identifier>
  ts: <timestamp>
  signal: merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked
  evidence_maturity: prompt-only | supported-signal | well-evidenced
  inventory_evidence_present: true | false
  evidence_basis:
    - overlap
    - successor-evidence
    - dependency-evidence
    - impact-reasoning
    - attribution-uncertainty
  impact_posture: worth-expanding | worth-keeping | keep-but-freeze | candidate-for-merge | candidate-for-retirement
  notes: <optional free text>
```

## Why shadow first

Reasons to keep this outside the core Ledger schema initially:
- governance signals are still advisory
- evidence maturity may be low
- inventory evidence may be missing
- lifecycle semantics are not yet executable

## Non-authoritative semantics

The shadow record means:
- this governance judgment was observed
- it was recorded with evidence qualifiers
- it should not be confused with an executed lifecycle transition

It does **not** mean:
- merge actually happened
- deprecation actually happened
- retirement is approved

## Promotion criteria

Only consider promoting governance_review toward Ledger-adjacent persistence if:
- runtime evaluations repeatedly surface stable signals
- evidence maturity is routinely recorded
- inventory-aware cases outperform prompt-only cases
- no repeated confusion occurs between signal vs state vs decision

## Promotion blockers

Do not promote if:
- governance signals are frequently emitted without evidence basis
- inventory evidence is usually absent
- runtime outputs confuse signal with lifecycle state
- impact posture is too unstable across similar cases

## Write discipline

Shadow records are per-run observations tied to a specific asset. They must not be interpreted as lifecycle facts, and they should not be collapsed into consensus without checking evidence maturity, inventory evidence, and conflict history.

For the repo-local Python harness, these files are semirun/test artifacts only. They are not Ledger substitutes, not host memory, and not evidence that merge/deprecate/retire actions or lifecycle transitions actually occurred.
