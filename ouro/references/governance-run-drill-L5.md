# Governance Run Drill — L5 (Inventory-aware governance)

> Controlled drill only. This is **not** a real host-emitted artifact and must not be treated as lifecycle fact.

## Source case

- From: `golden-tests.md`
- Case: `L5 — Inventory-aware governance should be stronger than prompt-only governance`

## Simulated interpretation

- `primary_decision`: `update-agent-md`
- `governance_signal`: `merge-candidate`
- `evidence_maturity`: `early-signal`
- `inventory_evidence_present`: `true`
- `impact_posture`: `candidate-for-merge`

## Why this case is a good first drill

1. It has a clear `asset_id`
2. It includes explicit inventory evidence
3. It exercises governance semantics without requiring lifecycle mutation
4. It is easy to see whether readers confuse `merge-candidate` with `merged`

## Companion artifact

- `governance-review-response-caution-rule-run-2026-05-21-L5.yaml`

## Pass criteria for this drill

- The artifact preserves all required fields
- The wording remains advisory, not factual
- The record can be clearly tied to one run and one asset
- A reader can distinguish `governance_signal` from lifecycle state
