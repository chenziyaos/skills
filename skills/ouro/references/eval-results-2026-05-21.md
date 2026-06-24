# Ouro — Evaluation Results (2026-05-21)

> Paper review run based on the current written contract, golden tests, and evaluation checklist. This is a spec-level assessment, not a live execution trace.

## Run metadata

- Date: 2026-05-21
- Reviewer: Codex (paper review)
- Ouro version: v1.1.5
- Host / environment: spec-only review against repository files
- Host mode: assumed `interactive`
- `host.memory.search`: assumed available in contract; B3 additionally checks degraded path
- `host.list_capabilities`: assumed optional / unspecified
- `host.exec` / sandbox: assumed optional / unspecified
- Ledger size bucket: `1-20` for baseline review; B3 explicitly covers degraded retrieval constraints
- Notes: Results below reflect expected behavior from the current design and wording, not an observed runtime transcript.

## Summary

| Section | Result | Notes |
|---|---|---|
| Trigger discipline | Pass | Trigger rules are now narrow enough to reject raw URL / food / generic ingest semantics. |
| Primary decisions | Pass | Decision mapping is explicit and aligned with golden cases. |
| Boundary tests | Pass | B1 and B2 have acceptable preferred outcomes; B3 degradation is explicitly visible in contract. |
| Contract observability | Pass | Confidence, degradation, rollback/containment, and Health Pulse minimum fields are defined. |
| Final release recommendation | Safe to release | No paper-level hard fail identified. |

## Case results

| Case | Trigger expected | Trigger actual | Decision expected | Decision actual | Confidence | Degradation visible? | Rollback / containment? | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|---|
| T1 | yes | yes | create/extend | create/extend | M | n/a | yes | Pass | Explicit `$ouro` + durable workflow should trigger. |
| T2 | yes | yes | add-rule/update-agent-md | add-rule/update-agent-md | M | n/a | yes | Pass | Capability-building intent without explicit skill name should still trigger. |
| T3 | no | no | n/a | n/a | n/a | n/a | n/a | Pass | Raw URL alone should stay on normal Q&A path. |
| T4 | no | no | n/a | n/a | n/a | n/a | n/a | Pass | Disambiguation examples in §17 block food / ingest semantics. |
| D1 | yes | yes | create-skill | create-skill | M | n/a | yes | Pass | Classic multi-step reusable workflow with rollback. |
| D2 | yes | yes | extend-skill | extend-skill | M | n/a | yes | Pass | Overlap / avoid-duplicate framing should prefer extension. |
| D3 | yes | yes | update-agent-md | update-agent-md | M | n/a | yes | Pass | Global behavior preference, not standalone workflow. |
| D4 | yes | yes | add-rule | add-rule | M | n/a | yes | Pass | Single enforceable compact rule maps to add-rule. |
| D5 | yes | yes | skip | skip | M | n/a | n/a | Pass | One-off knowledge should be skipped. |
| D6 | yes | yes | skip | skip | L | yes | n/a | Pass | Prompt injection / unsafe indirect instruction should force skip. |
| D7 | yes | yes | skip | skip | L | n/a | n/a | Pass | 主见原则 should reject vague intent. |
| B1 | yes | yes | update-agent-md | update-agent-md | M | n/a | yes | Pass | Preferred boundary outcome remains config-level behavior. |
| B2 | yes | yes | extend-skill | extend-skill | M | n/a | yes | Pass | Existing skill scope suggests extension unless overlap evidence is weak. |
| B3 | yes | yes | any (with visible degradation) | any (with visible degradation) | M | yes | yes | Pass | `retrieval_mode=context-only` and confidence ceiling are explicitly documented. |

## Findings

### Trigger regressions

- None identified in the written trigger contract.

### Decision regressions

- None identified in the written decision mapping.

### Observability / contract regressions

- None identified at paper-review level. Degradation and Health Pulse requirements are visible in the spec.

### Notable soft fails

- None in paper review. Runtime validation is still needed to confirm host-specific behavior and confidence calibration.

## Release recommendation

- Recommendation: Safe to release
- Reason: Trigger, decision, degradation, and reporting contracts are mutually consistent in the current repository version.
- Follow-up actions:
  - Run the same cases against a real host to validate runtime behavior.
  - Verify B3 under an actual `context-only` memory configuration.
  - Verify D6 / D7 remain strict after future trigger lexicon edits.
