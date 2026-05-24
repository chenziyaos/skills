# Ouro — Governance Run Artifact Emission Rules (Draft)

> Operational rules for emitting the first real `governance_review` artifact during runtime validation.

## Goal

Make the first write target practical and safe by specifying:
- when to emit
- when not to emit
- how to name the artifact
- what must be present before emission

## Emission condition

Emit a run-scoped governance artifact only if **all** of the following are true:

1. `Governance Signal != null`
2. the primary decision remains one of the five routing values
3. evidence envelope is complete:
   - `evidence_maturity`
   - `inventory_evidence_present`
   - `evidence_basis`
4. the language remains advisory (`candidate` / `blocked`), not state-factual
5. a stable `asset_id` can be named for the governed asset

## Do not emit when

Do **not** emit an artifact when any of the following hold:

- `Governance Signal = null`
- evidence basis is missing or partial
- the report wording collapses signal into lifecycle fact
- the asset under review is ambiguous
- attribution uncertainty is the dominant story but the output still tries to sound conclusive

## File naming convention

Recommended naming pattern:

```text
governance-review-<asset_id>-<run_id>.yaml
```

Examples:
- `governance-review-response-caution-rule-run-2026-05-21-001.yaml`
- `governance-review-report-writer-v1-run-2026-05-21-007.yaml`

## Storage convention

Recommended initial placement:
- alongside the run result artifact
- or in a run-scoped artifacts directory

Recommended properties:
- easy to inspect
- easy to delete
- not auto-merged into long-term memory
- clearly separate from Ledger records

## Companion relationship

If emitted, the governance artifact should be treated as a companion to a specific runtime result file.

Minimum cross-reference should be possible via:
- `run_id`
- `asset_id`
- timestamp

## Read discipline

Consumers of the artifact must assume:
- this is an observation from one run
- it may be superseded by later runs
- it is not evidence of an executed merge/deprecate/retire action

## Early-stage operational rule

Before any host-side automatic persistence is attempted, teams should prefer:
- manual or semi-manual artifact emission during runtime validation
- explicit review of emitted artifacts
- no automatic promotion into memory or Ledger-adjacent layers
