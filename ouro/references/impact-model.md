# Ouro — Impact Model (Draft)

> Draft model for deciding whether a capability change is worth keeping, merging, freezing, or retiring. This complements the lifecycle model by answering not just **what state an asset is in**, but **why the state is economically and operationally justified**.

## Purpose

The lifecycle model answers questions such as:
- Should this asset become stale / frozen / merged / deprecated / retired?

The impact model adds a second layer:
- Is that transition worth it?
- What value does the asset still create?
- What maintenance burden does it impose?
- How confident are we that the observed improvement came from this asset?

## Core dimensions

### 1. Expected benefit

How much durable value the asset is expected to create if kept active.

Suggested qualitative scale:
- `low`
- `mid`
- `high`

Typical signals:
- Prevents high-cost errors
- Improves output quality across many tasks
- Reduces repeated manual work
- Increases safety / clarity / consistency in a durable way

### 2. Maintenance cost

How much ongoing complexity the asset adds if kept active.

Suggested qualitative scale:
- `low`
- `mid`
- `high`

Typical signals:
- Requires frequent updates as environment changes
- Duplicates logic already present elsewhere
- Increases routing ambiguity or overlap
- Adds user or maintainer cognitive load

### 3. Affected scope

How broadly the asset influences behavior.

Suggested qualitative buckets:
- `local` — niche task / one workflow / one prompt family
- `team` — many related tasks in one domain
- `global` — broad default behavior across the agent

Why this matters:
- High-scope changes have higher upside
- High-scope changes also carry higher blast radius

### 4. Attribution confidence

How confident Ouro is that the observed benefit or harm is actually caused by this asset.

Suggested qualitative scale:
- `low`
- `mid`
- `high`

Typical signals:
- Was the change isolated from other changes?
- Do repeated successes/failures correlate with the asset?
- Is there a clear successor/predecessor comparison?
- Could the apparent improvement actually come from host/tool upgrades instead?

## Derived judgments

These are not schema requirements yet; they are reasoning outputs Ouro should be able to explain.

### A. Net value posture

A coarse synthesis of benefit vs cost.

Suggested labels:
- `worth-expanding`
- `worth-keeping`
- `keep-but-freeze`
- `candidate-for-merge`
- `candidate-for-retirement`

### B. Blast radius

A coarse synthesis of scope and risk.

Suggested labels:
- `contained`
- `moderate`
- `broad`

### C. Evidence maturity

How much runtime evidence exists behind the judgment.

Suggested labels:
- `prompt-only`
- `supported-signal`
- `well-evidenced`

## Decision heuristics

### Keep / expand

Prefer `active` or expansion when:
- expected benefit is `high`
- maintenance cost is `low` or `mid`
- attribution confidence is at least `mid`
- no clear overlap or successor exists

### Freeze

Prefer `frozen` when:
- expected benefit is still `mid` or `high`
- but maintenance or change cost is rising
- and the asset should remain available without further growth

### Merge

Prefer `merged` when:
- expected benefit mostly comes from semantics already present elsewhere
- maintenance cost is increased by duplication
- overlap is high enough that parallel growth harms clarity

### Deprecate / archive

Prefer `deprecated` or `archived` when:
- a successor exists
- the older asset still matters for audit / migration / compatibility
- but should no longer receive new extensions

### Retire

Prefer `retired` only when:
- expected benefit is low
- maintenance cost is not justified
- dependency risk is low
- rollback / replacement story is clear
- attribution confidence is at least `mid`

## Retirement blockers

Ouro should resist retirement when any of the following hold:
- The asset is safety-critical
- No successor exists
- Rollback path is unclear
- Usage is rare but consequence-weighted
- The observed burden is annoying but not materially harmful
- Attribution confidence is too low to justify removal

## Relationship to lifecycle

The lifecycle model provides the **state machine**.
The impact model provides the **economic and operational rationale** for transitions.

Examples:
- `active -> frozen` because benefit remains high but maintenance cost of continued expansion is no longer justified
- `active -> merged` because duplicated semantics make net value negative as a standalone asset
- `deprecated -> archived` because successor exists and blast radius of keeping both active is too broad
- `stale -> active` can happen if evidence reappears and benefit remains consequence-weighted

## Relationship to Ledger (future)

Not part of the formal schema yet, but likely future concepts include:
- `impact.expected_benefit`
- `impact.maintenance_cost`
- `impact.affected_scope`
- `impact.attribution_confidence`
- `impact.net_value_posture`

Until schema adoption, these concepts can live in:
- report reasoning
- review notes
- lifecycle evaluation references

## Suggested evaluation hooks

Future tests should include:
- High-benefit / high-cost asset that should be frozen rather than expanded
- Low-frequency / high-consequence asset that should remain stale/frozen, not retired
- Duplicate assets where merge is economically better than extension
- Apparent improvement with low attribution confidence that should not justify strong conclusions
