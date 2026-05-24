# Ouro — Shadow Write Protocol (Draft)

> Minimal write protocol for recording `governance_review` as a non-authoritative, run-scoped shadow artifact.

## Purpose

This protocol defines the smallest safe shape and write conditions for governance shadow persistence before any Ledger-adjacent promotion.

## Write target

Preferred initial targets:
- run-scoped result artifact
- host-side review note / shadow namespace

Not allowed initially:
- core Ledger `decision`
- lifecycle state fields
- any persistence path that makes advisory governance look authoritative

## Minimal write shape

```yaml
governance_review:
  asset_id: <stable asset identifier>
  run_id: <run identifier>
  ts: <timestamp>
  signal: merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked
  evidence_maturity: design-intent | early-signal | well-evidenced
  inventory_evidence_present: true | false
  evidence_basis:
    - overlap
    - successor-evidence
    - dependency-evidence
    - impact-reasoning
    - attribution-uncertainty
  impact_posture: worth-expanding | worth-keeping | keep-but-freeze | candidate-for-merge | candidate-for-retirement
  notes: <optional>
```

## Write preconditions

A shadow write may occur only if:
1. a governance signal is actually surfaced in the report
2. the five-way primary decision remains unchanged
3. the evidence envelope is complete
4. the signal is expressed as advisory language, not lifecycle fact
5. asset identity is explicit enough to support later comparison

## Write blockers

Do not write if:
- `signal` is absent
- `signal` exists but evidence envelope is incomplete
- the report wording collapses signal into lifecycle state
- the asset under review cannot be identified

## Aggregation discipline

Shadow records are append-only observations, not final truth.

When multiple records exist for the same `asset_id`:
- do not collapse by count alone
- prefer later records only when evidence maturity is not worse
- conflicting recent signals should block promotion
- repeated low-quality signals do not equal stable governance truth

## Read discipline

Consumers of shadow records must read them as:
- governance observations
- with evidence qualifiers
- tied to a specific run and asset

They must not read them as:
- executed lifecycle transitions
- direct replacement for `decision`
- proof that a merge/deprecate/retire action already happened

## Read model for future promotion

If future systems want to promote shadow data toward stronger persistence, they should ask:
1. Is the signal stable across multiple runs for the same asset?
2. Is evidence maturity improving rather than degrading?
3. Is inventory evidence present in the stronger records?
4. Are conflicting recent signals unresolved?

If these questions cannot be answered clearly, promotion should be blocked.
