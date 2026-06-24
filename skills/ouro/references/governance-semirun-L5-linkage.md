# Governance Semirun Linkage — L5

> Readback note for the semi-real runtime package using case `L5`.

## Package contents

1. Main runtime result:
   - `eval-results-runtime-hostA-L5-semirun-2026-05-21.md`
2. Companion governance artifact:
   - `governance-review-response-caution-rule-run-2026-05-21-L5.yaml`
3. Drill rationale:
   - `governance-run-drill-L5.md`

## How to read the package

### Step 1 — Read the main runtime result first
The main result answers:
- what the primary decision was
- whether governance reasoning appeared
- whether the run is acceptable at runtime-eval level

### Step 2 — Read the governance artifact second
The artifact answers:
- which asset the governance observation is about
- what governance signal was surfaced
- what evidence envelope supported it

### Step 3 — Keep the semantic boundary intact
The package should be read as:
- runtime result = main run outcome
- governance artifact = companion governance observation

It should **not** be read as:
- governance artifact = lifecycle state fact
- governance artifact = executed merge/deprecate action

## What this semirun proves

- A non-null governance signal can be emitted without changing the five-way primary decision
- A companion governance artifact can carry richer structure than the main runtime result
- Inventory-backed governance can be stronger than prompt-only governance while still remaining advisory

## What it does not prove

- That host runtime will emit the same fields automatically
- That a long-term memory or Ledger-adjacent write is safe yet
- That governance aggregation across runs is already solved
