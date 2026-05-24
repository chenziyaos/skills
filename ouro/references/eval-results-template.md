# Ouro — Evaluation Results Template

> Copy this file per regression run, e.g. `eval-results-2026-05-21.md`.

## Run metadata

- Date:
- Reviewer:
- Ouro version:
- Host / environment:
- Host mode:
- `host.memory.search`:
- `host.list_capabilities`:
- `host.exec` / sandbox:
- Ledger size bucket: `0` / `1-20` / `21+`
- Notes:

## Summary

| Section | Result | Notes |
|---|---|---|
| Trigger discipline | TBD | |
| Primary decisions | TBD | |
| Boundary tests | TBD | |
| Lifecycle governance | TBD | |
| Contract observability | TBD | |
| Final release recommendation | TBD | |

## Case results

| Case | Trigger expected | Trigger actual | Decision expected | Decision actual | Confidence | Degradation visible? | Rollback / containment? | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|---|
| T1 | yes |  | create/extend |  |  |  |  |  |  |
| T2 | yes |  | add-rule/update-agent-md |  |  |  |  |  |  |
| T3 | no |  | n/a |  |  |  |  |  |  |
| T4 | no |  | n/a |  |  |  |  |  |  |
| T5 | no |  | n/a |  |  |  |  |  |  |
| T6 | no |  | n/a |  |  |  |  |  |  |
| T7 | yes |  | update-agent-md/add-rule |  |  |  |  |  |  |
| T8 | yes |  | create-skill |  |  |  |  |  |  |
| T9 | yes |  | extend-skill |  |  |  |  |  |  |
| T10 | yes |  | update-agent-md/add-rule |  |  |  |  |  |  |
| D1 | yes |  | create-skill |  |  |  |  |  |  |
| D2 | yes |  | extend-skill |  |  |  |  |  |  |
| D3 | yes |  | update-agent-md |  |  |  |  |  |  |
| D4 | yes |  | add-rule |  |  |  |  |  |  |
| D5 | yes |  | skip |  |  |  |  |  |  |
| D6 | yes |  | skip |  |  |  |  |  |  |
| D7 | yes |  | skip |  |  |  |  |  |  |
| B1 | yes |  | update-agent-md |  |  |  |  |  |  |
| B2 | yes |  | extend-skill |  |  |  |  |  |  |
| B3 | yes |  | any (with visible degradation) |  |  |  |  |  |  |

## Lifecycle case results

| Case | Lifecycle expected | Governance / lifecycle actual | Evidence maturity | Inventory evidence present? | Verdict | Notes |
|---|---|---|---|---|---|---|
| L1 | merge/freeze signal |  |  |  |  |  |
| L2 | stale/frozen, not retired |  |  |  |  |  |
| L3 | deprecated/archive signal |  |  |  |  |  |
| L4 | retirement blocked by safety |  |  |  |  |  |

## Shadow artifact emission

- `run_result.json` written?:
- Companion governance artifact emitted?:
- Artifact path/name:
- `outputPolicy.outputMode`:
- `outputPolicy.cacheTtlHours`:
- `outputPolicy.expiredRunDirsRemovedCount`:
- `outputPolicy.expiredRunDirsSample`:
- `outputPolicy.cleanupWarnings`:
- `observability.scoreBreakdown` checked?:
- `observability.decisionExplanation` checked?:

## Findings

### Trigger regressions

-

### Decision regressions

-

### Lifecycle governance regressions

-

### Observability / contract regressions

-

### Notable soft fails

-

## Release recommendation

- Recommendation: Safe to release / Release with note / Block release
- Reason:
- Follow-up actions:
