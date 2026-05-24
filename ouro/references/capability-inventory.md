# Ouro — Capability Inventory (Draft)

> Minimal asset inventory draft for moving lifecycle governance from prompt-only reasoning toward asset-aware governance.

## Purpose

Current lifecycle judgments often rely on the prompt explicitly describing:
- whether a successor exists
- whether dependencies exist
- whether an asset is safety-critical

This inventory draft is the smallest structure that can support stronger merge / deprecate / retire reasoning without introducing a full database or graph system.

## Minimal fields

| Field | Meaning |
|---|---|
| `asset_id` | Stable identifier of the capability asset |
| `asset_type` | `skill` / `agent-md` / `rule` / `prompt-asset` / `eval-asset` |
| `scope` | `local` / `team` / `global` |
| `successor_of` / `merged_into` | Optional lineage relationship |
| `depends_on` | Other assets or assumptions this asset relies on |

## Optional future fields

These are intentionally out of scope for the minimal draft, but likely future additions:
- `owner`
- `safety_critical`
- `compatibility_role`
- `rollback_path`
- `usage_signal`
- `status` (active / stale / frozen / deprecated / archived / retired)
- impact summary fields

## Example fragment

```yaml
assets:
  - asset_id: risk-first-agent-md
    asset_type: agent-md
    scope: global
    successor_of: null
    merged_into: null
    depends_on: []

  - asset_id: response-caution-rule
    asset_type: rule
    scope: global
    successor_of: null
    merged_into: risk-first-agent-md
    depends_on: [risk-first-agent-md]

  - asset_id: report-writer-v1
    asset_type: skill
    scope: team
    successor_of: null
    merged_into: null
    depends_on: []

  - asset_id: report-writer-v2
    asset_type: skill
    scope: team
    successor_of: report-writer-v1
    merged_into: null
    depends_on: []
```

## Governance rule of thumb

If inventory / successor / dependency evidence is missing, Ouro should degrade retirement-style judgments from:
- strong recommendation

to:
- `candidate` language only

Examples:
- `merge-candidate`
- `deprecate-candidate`
- `retirement-blocked`

This avoids over-claiming governance confidence when the asset graph is not visible.

## Suggested uses

The inventory draft is intended to support:
- lifecycle reviews
- conflict resolution
- merge/deprecate/retire tests
- future capability portfolio optimization

## Suggested evaluation hooks

Future tests should include inventory-aware cases such as:
- successor exists in inventory but migration cost is high
- merge candidate confirmed by both overlap and explicit dependency structure
- retirement blocked because another active asset depends on the target
