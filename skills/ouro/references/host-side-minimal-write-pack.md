# Ouro — Host-Side Minimal Write Pack (Draft)

> Practical preparation pack for the first real host-side governance shadow write.

## Objective

Run one real host-side case that produces:
1. a normal runtime result
2. a companion run-scoped governance artifact
3. a clear linkage between the two

without:
- changing the five-way primary decision contract
- treating governance signal as lifecycle fact
- touching Ledger core schema

## Recommended first case

Use case:
- `L5 — Inventory-aware governance should be stronger than prompt-only governance`

Why this case first:
- explicit `asset_id` exists (`response-caution-rule`)
- inventory evidence is present
- governance signal is meaningful (`merge-candidate`)
- no lifecycle mutation is needed
- easy to read and explain

## Expected outputs

### 1. Main runtime result
Recommended file shape:
- start from `eval-results-runtime-hostA-L5-semirun-2026-05-21.md`
- replace semirun assumptions with actual host observations

### 2. Companion governance artifact
Recommended file shape:
- start from `governance-run-artifact-template.yaml`
- target naming pattern:
  - `governance-review-<asset_id>-<run_id>.yaml`

### 3. Linkage note
Recommended file shape:
- start from `governance-semirun-L5-linkage.md`
- explain how to read runtime result vs companion artifact

## Write sequence

1. Run the real host-side case
2. Fill the runtime result first
3. Check whether `Governance Signal != null`
4. Check whether the evidence envelope is complete
5. Only then emit the companion governance artifact
6. Add or update linkage/readback note

## Minimal fields that must be observed in the host run

### In the main runtime result
- primary decision
- governance signal (if any)
- evidence maturity
- inventory evidence present
- evidence basis
- confidence

### In the governance artifact
- `asset_id`
- `run_id`
- `ts`
- `primary_decision`
- `signal`
- `evidence_maturity`
- `inventory_evidence_present`
- `evidence_basis`
- `impact_posture`

## Success criteria

A first host-side write is successful if all of the following are true:

1. The host run still preserves a valid five-way `Decision`
2. A non-null governance signal is surfaced only as advisory language
3. The companion governance artifact is emitted only after the evidence envelope is complete
4. The runtime result and artifact can be linked by `run_id` and `asset_id`
5. A reader can clearly distinguish:
   - runtime result = run outcome
   - governance artifact = governance observation
6. No wording implies an executed merge/deprecate/retire action

## Hard fail signals

Abort or mark the run invalid if any of these happen:
- `Decision` is replaced by a governance signal
- governance signal is written without evidence maturity / evidence basis
- artifact is emitted even though `Governance Signal = null`
- wording collapses `merge-candidate` into `merged`, `freeze-candidate` into `frozen`, etc.
- artifact cannot be tied to a stable `asset_id` and `run_id`

## Recommended review questions after the run

1. Did the host produce the governance-aware fields naturally, or only through heavy manual patching?
2. Was the artifact easy to read without confusing it for lifecycle fact?
3. Did inventory evidence actually make the governance judgment stronger and clearer?
4. Would a second reviewer interpret the package the same way?

## Next-case progression

If L5 succeeds, the next two cases should be:
- `I1` (`freeze-candidate`)
- `L4` (`retirement-blocked`)

This validates the other two high-risk governance signals before any broader rollout.

## Companion short checklist

For the shortest execution path, use `host-side-first-run-checklist.md`.
