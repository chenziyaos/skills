# Ouro — Protocol Upgrade Draft

> Draft for upgrading Ouro from a pure five-way routing contract toward a layered governance-aware contract, without immediately breaking compatibility.

## Goal

Preserve the current primary decision contract while making governance reasoning first-class enough to be:
- visible
- structured
- comparable across runs
- eventually recordable next to Ledger decisions

## Current protocol shape

Today, Ouro has:
- a five-way primary decision taxonomy
- lifecycle reasoning in references/tests
- impact reasoning in references/tests
- governance_signal in reference/eval/runtime layers only

What is missing is a stable protocol slot for governance outputs.

## Proposed layering

### Layer 1 — Primary decision (unchanged)
One of:
- `create-skill`
- `extend-skill`
- `update-agent-md`
- `add-rule`
- `skip`

### Layer 2 — Governance signal (new structured advisory layer)
One of:
- `merge-candidate`
- `freeze-candidate`
- `deprecate-candidate`
- `retirement-blocked`
- `null`

### Layer 3 — Evidence envelope (new supporting layer)
- `evidence_maturity`: `design-intent | early-signal | well-evidenced`
- `inventory_evidence_present`: `true | false`
- `evidence_basis`: overlap / successor-evidence / dependency-evidence / impact-reasoning / attribution-uncertainty

### Layer 4 — Lifecycle state (still not directly mutated by the report)
Lifecycle states remain reference/asset concepts, not direct output facts unless future governance execution exists.

## Report upgrade proposal

A future report-compatible extension could add:

```yaml
Decision: <five-way primary decision>
Governance Signal: <null | merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked>
Evidence Maturity: <design-intent | early-signal | well-evidenced>
Inventory Evidence Present: <true | false>
Evidence Basis: [<one or more short reasons>]
```

This preserves backward compatibility because:
- the primary Decision field stays unchanged
- governance is advisory, not executable

## Ledger-adjacent upgrade proposal

Do **not** put governance signals directly into the core schema first.

Preferred sequence:
1. Report / evaluation assets
2. Result templates / runtime records
3. Ledger-adjacent review notes or shadow structure
4. Only later: formal schema candidate

A future shadow shape might be:

```yaml
governance_review:
  signal: merge-candidate
  evidence_maturity: early-signal
  inventory_evidence_present: false
  evidence_basis:
    - overlap
    - impact-reasoning
```

## Upgrade constraints

- Governance signal must never replace primary decision
- Governance signal must never be treated as an executed lifecycle transition
- Missing inventory/successor/dependency evidence must force candidate/blocking language
- Low attribution confidence must prevent strong value conclusions

## Recommended upgrade order

### Stage 1 — advisory protocol
- make governance_signal visible in reports and runtime records

### Stage 2 — recorded protocol
- stabilize fields in eval/runtime results and paper review outputs

### Stage 3 — shadow persistence
- allow governance_review as a Ledger-adjacent, non-authoritative structure

### Stage 4 — schema candidate
- only if signals are stable under runtime validation

## Exit criteria before touching core schema

Only consider a formal schema change when:
- governance signals are stable across multiple runtime runs
- evidence maturity discipline is respected
- inventory-backed cases outperform prompt-only governance cases
- no repeated confusion occurs between signal vs state vs decision
