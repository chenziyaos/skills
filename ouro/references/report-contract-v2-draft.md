# Ouro — CogniVore Report v2 (Draft)

> Draft report contract for surfacing governance reasoning without breaking the existing five-way decision contract.

## Design goal

Keep the current report compatible with the existing primary decision model, while making governance reasoning:
- visible
- structured
- evidence-aware
- comparable across manual and runtime evaluation

## v1 report core

Current report core is effectively:
- Input Type
- Core Value
- Decision
- Confidence
- Ledger ID
- Endure / Discover / Die-Back / Mirror Scan / Rewrite Plan / Probe / Health Pulse / Next Action

## v2 extension principle

Do not replace the v1 core.
Add a governance extension block that is:
- optional
- advisory
- evidence-aware

## Proposed v2 header additions

```yaml
Decision: <five-way primary decision>
Governance Signal: <null | merge-candidate | freeze-candidate | deprecate-candidate | retirement-blocked>
Evidence Maturity: <design-intent | early-signal | well-evidenced>
Inventory Evidence Present: <true | false>
Evidence Basis: [<overlap | successor-evidence | dependency-evidence | impact-reasoning | attribution-uncertainty>]
Confidence: <H | M | L>
```

## Placement in report

Recommended placement:

1. Keep `Decision` in the main summary area
2. Add governance extension immediately after Decision / Confidence
3. Expand reasoning in either:
   - `Mirror Scan`
   - `Rewrite Plan`
   - or a new optional subsection: `Governance Review`

## Optional Governance Review block

```markdown
### Governance Review
Signal: `merge-candidate`
Evidence maturity: `early-signal`
Inventory evidence present: `false`
Evidence basis: overlap, impact-reasoning
Reason: overlap is high and duplicate semantics increase maintenance cost, but no explicit inventory graph is available, so the signal stays advisory.
```

## Output discipline

v2 must preserve these invariants:

- `Decision` remains the only routing output
- `Governance Signal` is advisory, not executable
- `Governance Signal` does not imply lifecycle state mutation
- missing inventory/successor/dependency evidence forces weaker governance language
- low attribution confidence prevents strong value claims
- repo-local Python shadow output may validate report shape, but it must not promote advisory governance into lifecycle machine facts

## Recommended mappings

### Example 1 — extension with freeze pressure
- Decision: `extend-skill`
- Governance Signal: `freeze-candidate`
- Why: benefit remains high, maintenance cost rising

### Example 2 — skip with retirement blocked
- Decision: `skip`
- Governance Signal: `retirement-blocked`
- Why: safety-critical rule, no successor, rollback unclear

### Example 3 — update-agent-md with merge pressure
- Decision: `update-agent-md`
- Governance Signal: `merge-candidate`
- Why: duplicated semantics between rule and config layer

## Compatibility strategy

v2 should be introduced in stages:

### Stage 1 — documentation + evaluation only
- present in paper review outputs
- present in runtime result skeletons

### Stage 2 — optional runtime report field
- hosts may surface governance extension when evidence is available

### Stage 3 — stable contract candidate
- only after repeated runtime validation shows the field is understandable and useful

## Non-goals for v2

- Do not add executable merge/deprecate/retire actions yet
- Do not promote governance signals into the primary decision taxonomy
- Do not require immediate Ledger schema changes
