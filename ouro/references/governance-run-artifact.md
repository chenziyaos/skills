# Ouro — Governance Run Artifact (Draft)

> First real write target for `governance_review`: a run-scoped artifact that records governance reasoning without pretending to be durable system truth.

## Why this target first

A run-scoped artifact is the safest first write target because it:
- keeps governance reasoning tied to one run
- is easy to inspect and discard
- minimizes semantic bleed into Ledger or lifecycle facts
- provides real data for later comparison without forcing early schema decisions

## Intended use

This artifact should be emitted only when a run surfaces a non-null governance signal.

It is suitable for:
- runtime experiments
- semirun outputs that want structured governance evidence
- paper review outputs that compare advisory governance observations
- future aggregation experiments outside the core Ledger

It is not suitable for:
- direct replacement of primary decision storage
- lifecycle state mutation
- authoritative long-term memory by default
- any claim that governance state has been durably persisted

## Minimal artifact shape

```yaml
governance_review:
  asset_id: <stable asset identifier>
  run_id: <run identifier>
  ts: <timestamp>
  primary_decision: create-skill | extend-skill | update-agent-md | add-rule | skip
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

## Field rationale

- `asset_id`: required to compare governance records for the same asset across runs
- `run_id`: required to keep records per-run and avoid false consensus by accidental merge
- `ts`: required for ordering and later comparison
- `primary_decision`: preserves the routing context around the governance signal
- `signal`: the governance posture itself
- `evidence_maturity`: prevents weak signals from looking authoritative
- `inventory_evidence_present`: distinguishes prompt-only from asset-aware reasoning
- `evidence_basis`: preserves the reason types behind the signal
- `impact_posture`: keeps the why-layer close to the governance conclusion

## What should not be added yet

Avoid adding these in the first real artifact:
- final lifecycle state
- authoritative successor resolution
- auto-merge or auto-retire booleans
- direct links to Ledger `outcome`
- aggressive aggregation counters

These would make the artifact look more authoritative than it should be.

## Emission rule

Emit the artifact only when:
- `Governance Signal != null`
- the evidence envelope is complete
- the primary decision remains unchanged

If any of these fail, prefer no artifact over a weak or ambiguous artifact.

## Read rule

Consumers must read this artifact as:
- a run-bound governance observation
- not a lifecycle fact
- not a durable truth unless later promoted by separate rules
