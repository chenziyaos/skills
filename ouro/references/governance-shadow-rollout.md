# Ouro — Governance Shadow Rollout (Draft)

> Rollout plan for moving `governance_review` from design artifact to safe, non-authoritative runtime recording, without prematurely promoting it into the core Ledger schema.

## Goal

Introduce governance persistence in a way that is:
- observable
- reversible
- clearly weaker than lifecycle facts
- safe under incomplete evidence

## Key principle

`governance_review` should become **recorded before it becomes authoritative**.

In practice, this means:
1. first visible in report outputs
2. then recorded in evaluation/runtime artifacts
3. then optionally persisted in a shadow structure
4. only much later considered for Ledger-adjacent or schema-candidate status

## Rollout stages

### Stage 0 — narrative only
Current/initial state:
- governance ideas exist in references and examples
- no persistence
- no structured runtime write path

### Stage 1 — report-visible only
Allowed behavior:
- `Governance Signal`
- `Evidence Maturity`
- `Inventory Evidence Present`
- `Evidence Basis`
may appear in `CogniVore Report`

Constraints:
- advisory only
- no persistence semantics implied
- no lifecycle mutation implied

### Stage 2 — evaluation/runtime recorded
Allowed behavior:
- governance fields appear in:
  - `eval-results-template.md`
  - runtime result skeletons
  - paper review outputs

Constraints:
- used for comparison and regression
- still not treated as system facts
- expected to retain candidate/blocking language when evidence is incomplete

### Stage 3 — shadow persistence candidate
Allowed behavior:
- host or tooling may store a `governance_review` shadow record next to a run result
- shadow record is non-authoritative and review-oriented

Minimum required fields:
- `signal`
- `evidence_maturity`
- `inventory_evidence_present`
- `evidence_basis`

Recommended additional fields:
- `impact_posture`
- `notes`
- timestamp / run identifier

### Stage 4 — Ledger-adjacent persistence
Allowed behavior:
- governance review may be attached to Ledger-adjacent notes or shadow namespaces
- still must not overwrite `decision`
- still must not be treated as lifecycle fact

Promotion gates:
- repeated runtime stability
- no recurring confusion between signal vs state vs decision
- inventory-aware cases reliably outperform prompt-only governance cases
- evidence maturity routinely captured

### Stage 5 — schema-candidate review
Only at this point should the team consider:
- formalizing a stable governance_review structure for long-term storage
- defining migration/versioning semantics
- evaluating whether any fields should enter a schema candidate layer

## Write boundary

`governance_review` may be written only when all of the following hold:
- a governance signal is actually surfaced
- evidence basis is visible
- evidence maturity is recorded
- the output still preserves the original five-way primary decision unchanged

It must **not** be written as a lifecycle fact.

## Candidate vs strong language rules

Use stronger advisory recording only when:
- successor/dependency/inventory evidence is present
- impact reasoning is explicit
- attribution uncertainty is not dominant

Default to weaker language when:
- inventory evidence is absent
- successor is implied but not demonstrated
- the apparent benefit may come from host/model changes

## Promotion blockers

Do not advance beyond evaluation/runtime recording if any of these persist:
- governance signal emitted without evidence basis
- inventory evidence usually absent
- runtime outputs confuse signal with lifecycle state
- users/readers misinterpret signal as an executed action
- impact posture is unstable across similar cases

## Shadow-specific safety gates

### Gate 1 — Signal/state separation
A shadow write is invalid if the record could be read as a lifecycle fact rather than an advisory signal.

Minimum rule:
- `merge-candidate != merged`
- `freeze-candidate != frozen`
- `deprecate-candidate != deprecated`
- `retirement-blocked` is not a lifecycle state

### Gate 2 — Evidence envelope completeness
A shadow write is invalid if `signal != null` but any of the following are missing:
- `evidence_maturity`
- `inventory_evidence_present`
- `evidence_basis`

No bare signal-only persistence is allowed.

### Gate 3 — Asset identity and ordering
A shadow write is unsafe unless it is bound to a stable asset reference and is orderable.

Minimum write metadata should allow answering:
- which asset is being reviewed?
- which run produced this record?
- is this newer or older than another record for the same asset?

Without this, repeated records can accumulate into false consensus.

## Promotion block rules

Promotion beyond runtime/result recording must be blocked when:
- a signal is present without a full evidence envelope
- inventory/dependency/successor evidence is missing but the language is stronger than candidate/blocking
- the same asset has conflicting recent governance signals without explicit resolution
- runtime readers could plausibly confuse signal with lifecycle fact

## Recommended first real write target

If real persistence is attempted, the safest first write target is:
- run-scoped result artifact
- or host-side review note / shadow namespace

Not recommended first targets:
- core Ledger schema
- primary decision field
- lifecycle state field

## Minimal run-scoped shadow example

```yaml
governance_review:
  signal: merge-candidate
  evidence_maturity: supported-signal
  inventory_evidence_present: false
  evidence_basis:
    - overlap
    - impact-reasoning
  impact_posture: candidate-for-merge
  notes: duplicate semantics are raising maintenance ambiguity, but no authoritative inventory graph is available
```

## Success criteria for rollout

A rollout is ready for the next stage when:
- governance signals remain understandable in repeated runs
- evidence quality is captured consistently
- inventory-aware cases produce measurably stronger governance confidence than prompt-only cases
- no strong governance conclusion is emitted under clearly weak evidence
