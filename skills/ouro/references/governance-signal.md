# Ouro — Governance Signal (Draft)

> Draft layer for expressing governance-oriented judgments without immediately expanding Ouro's primary decision taxonomy.

## Purpose

Ouro's current primary decisions answer:
- `create-skill`
- `extend-skill`
- `update-agent-md`
- `add-rule`
- `skip`

These are **routing decisions**.

Lifecycle and impact reasoning introduce another class of output:
- merge candidate
- freeze candidate
- deprecate candidate
- retirement blocked

These are not yet first-class decisions; they are **governance signals** that explain how an asset portfolio should be managed around the primary decision.

## Layering model

### 1. Primary decision
Answers: *where should this input land now?*

Examples:
- `extend-skill`
- `skip`
- `update-agent-md`

### 2. Governance signal
Answers: *what governance posture should surround that decision?*

Examples:
- `merge-candidate`
- `freeze-candidate`
- `deprecate-candidate`
- `retirement-blocked`

### 3. Lifecycle state
Answers: *what is the current or target lifecycle state of an asset?*

Examples:
- `active`
- `stale`
- `frozen`
- `deprecated`
- `archived`

### 4. Impact model
Answers: *why is the governance posture justified?*

Examples:
- high expected benefit
- rising maintenance cost
- broad scope / blast radius
- low attribution confidence

## Minimal initial signal set

These are the smallest signals worth standardizing first:

| Signal | Meaning | Typical use |
|---|---|---|
| `merge-candidate` | This asset should likely be merged with another rather than continued in parallel | duplication / overlap / routing ambiguity |
| `freeze-candidate` | Keep the asset, but stop expanding it for now | high benefit but rising maintenance cost |
| `deprecate-candidate` | A successor exists; this asset should stop receiving new growth | successor / migration path exists |
| `retirement-blocked` | Retirement may look attractive, but is unsafe or under-evidenced | safety-critical / missing successor / weak evidence |

## Output discipline

Governance signals should initially be treated as:
- **structured advisory outputs**
- not executable state transitions
- not replacements for the primary decision

This keeps Ouro compatible with the existing five-way decision contract while still making governance reasoning auditable.

## Evidence discipline

A governance signal should be downgraded to candidate language when evidence is weak.

Examples:
- Missing successor / dependency evidence -> do not claim deprecate/retire strongly
- Low attribution confidence -> do not claim worth-expanding strongly
- No inventory view -> use `merge-candidate`, not `merged`

## Minimal field shape (future-facing)

If governance signals later graduate from narrative-only output into structured records, the smallest useful shape is likely:

```yaml
governance_signal:
  kind: merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked
  evidence_maturity: prompt-only | supported-signal | well-evidenced
  inventory_evidence_present: true | false
  evidence_basis:
    - overlap
    - successor-evidence
    - dependency-evidence
    - impact-reasoning
    - attribution-uncertainty
```

### Why these fields first

- `kind` gives the governance posture itself
- `evidence_maturity` prevents weak signals from looking like settled facts
- `inventory_evidence_present` separates prompt-only reasoning from asset-aware reasoning
- `evidence_basis` preserves why the signal was emitted

This is intentionally smaller than a full lifecycle or Ledger schema extension.

## Recommended placements

In the near term, governance signals should appear in:
1. `CogniVore Report` reasoning sections
2. `eval-results-template.md`
3. runtime result skeletons

They should **not yet** be promoted to:
- primary decision taxonomy
- formal lifecycle transitions in Ledger schema

until runtime validation shows the signals are stable and interpretable.

## Upgrade path

### Stage 1 — advisory
- signals only in reports and evaluation assets

### Stage 2 — recorded
- signals become structured fields in result records / review notes

### Stage 3 — schema-candidate
- stable signals may be promoted into Ledger-adjacent fields

### Stage 4 — executable governance
- only after strong evidence and rollback discipline exist

## Main risks

### Risk 1: taxonomy explosion
If governance signals are promoted too early into the main decision layer, Ouro may become harder to route and evaluate.

### Risk 2: false governance confidence
If signals are emitted without inventory / impact / successor evidence, the system may sound more certain than it really is.
