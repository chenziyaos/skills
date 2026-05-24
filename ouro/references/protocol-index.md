# Ouro — Protocol Assets Index

> Navigation index for protocol-evolution references.

## Reader paths
- Shadow runtime contract: `../SKILL.md §7.2` → `shadow-runtime-contract.md` → `runtime-checklist.md` → `golden-tests.md` → `eval-checklist.md` → `eval-results-template.md`
- Shadow runtime explainability / retention: `../SKILL.md §7.2` → `shadow-runtime-contract.md` → `runtime-checklist.md` → `host-adapter.md`
- Host adapter and capability schema: `../SKILL.md §10` → `host-adapter.md`
- Governance semantics: `governance-signal.md` → `capability-lifecycle.md` → `impact-model.md`
- Upgrade planning: `protocol-upgrade-draft.md` → `governance-shadow-rollout.md` → `shadow-write-protocol.md`

## Governance semantics
- `governance-signal.md` — defines governance signals as a secondary advisory layer
- `capability-lifecycle.md` — defines lifecycle states and transitions
- `impact-model.md` — defines benefit / cost / scope / attribution reasoning
- `capability-inventory.md` — defines the minimal asset inventory draft

## Upgrade drafts
- `protocol-upgrade-draft.md` — staged upgrade path from routing-only to governance-aware protocol
- `report-contract-v2-draft.md` — draft report contract for governance-aware output
- `report-examples-v2.md` — concrete report examples using governance_signal
- `governance-shadow-rollout.md` — staged rollout plan for non-authoritative governance persistence
- `shadow-write-protocol.md` — minimal write protocol for run-scoped governance shadow records
- `shadow-target-selection.md` — comparison of first real write targets for governance shadow persistence
- `governance-run-artifact.md` — first real write target spec for run-scoped governance shadow output
- `governance-run-artifact-template.yaml` — minimal YAML template for the first write target
- `governance-run-artifact-example.yaml` — concrete example of a run-scoped governance artifact
- `governance-run-artifact-emission.md` — emission rules for the first real write target

## Suggested reading order
1. `governance-signal.md`
2. `capability-lifecycle.md`
3. `impact-model.md`
4. `capability-inventory.md`
5. `protocol-upgrade-draft.md`
6. `report-contract-v2-draft.md`
7. `report-examples-v2.md`
8. `governance-shadow-rollout.md`
9. `shadow-write-protocol.md`
10. `shadow-target-selection.md`
11. `governance-run-artifact.md`
12. `governance-run-artifact-template.yaml`
13. `governance-run-artifact-example.yaml`
14. `governance-run-artifact-emission.md`

## Host-side trial assets
- `host-side-minimal-write-pack.md` — preparation pack for the first real host-side write
- `host-side-minimal-write-checklist.md` — detailed execution checklist
- `host-side-first-run-checklist.md` — shortest first-run checklist
