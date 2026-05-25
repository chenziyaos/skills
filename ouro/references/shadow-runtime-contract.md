# Ouro — Shadow Runtime Contract

> Stable reference for the repo-local advisory-only shadow runtime. Source of truth for the broader protocol remains `../SKILL.md`; this file narrows that down to the current Python semirun surface.

## Scope

This contract describes only the repo-local Python shadow runtime. It does **not** describe the full normative Ouro protocol, durable Ledger semantics, or mutation-capable host integrations.

## CLI flags

Core inputs:
- `--prompt`
- `--input-file`
- `--asset-inventory-file`
- `--output-dir`

Shadow host snapshot flags:
- `--host-memory-search`
- `--host-list-capabilities`
- `--host-exec`
- `--host-bridge-file`
- `--ledger-size-bucket`

Shadow observability / retention flags:
- `--show-scores`
- `--explain-decision`
- `--cache-ttl-hours`

## JSON success result

Minimum top-level fields:
- `schemaVersion`
- `mode`
- `runId`
- `ts`
- `input`
- `host`
- `trigger`
- `decision`
- `confidence`
- `retrievalMode`
- `degradations`
- `priorEvidence`
- `evidence`
- `probe`
- `controlPlane`
- `shadowBoundary`
- `report`
- `governanceReview`
- `observability`
- `outputPolicy`
- `artifacts`

Fields that are always present but may be `null` in a successful shadow run include `decision`, `confidence`, `observability`, and `outputPolicy`.

### Invariants

- `mode` is always `shadow`
- `runId` and `ts` come from the same run-scoped context
- `host.readOnly` stays `true`
- `shadowBoundary.advisoryOnly` stays `true`
- `shadowBoundary` mutation flags remain `false`
- `probe.mode` is only `report-only` or `available-but-not-executed`
- `controlPlane` remains advisory-only and is triggered from direct user text only; protected quoted / fenced / source-tagged content is data, not a control directive
- Companion governance artifacts are advisory run-scoped observations, never lifecycle facts

## Observability contract

`observability` may be `null`.

When `--show-scores` is enabled:
- `observability.showScores = true`
- `observability.scoreBreakdown` contains the five routing classes

When `--explain-decision` is enabled:
- `observability.explainDecision = true`
- `observability.decisionExplanation.triggerReason`
- `observability.decisionExplanation.triggerEvidence`
- `observability.decisionExplanation.topDecision`
- `observability.decisionExplanation.runnerUpDecision`
- `observability.decisionExplanation.boundaryAmbiguity`
- `observability.decisionExplanation.boundaryDetail`
- `observability.decisionExplanation.signalBuckets`

## Prior-evidence contract

`priorEvidence` is always present.

It is the shadow runtime's read-only advisory prior summary layer, not a substitute for the host-side Ledger contract.

Minimum fields:
- `mode`
- `readOnly`
- `ledgerPriorsPresent`
- `ledgerPriorCount`
- `unresolvedCount`
- `decisionCounts`
- `outcomeCounts`
- `notes`

Rules:
- `readOnly` remains `true`
- this section expresses advisory confidence inputs only, not durable ledger mutation or lifecycle state
- `ledgerPriorCount` and `unresolvedCount` are integers
- `decisionCounts` and `outcomeCounts` are string-to-integer maps
- `notes` must preserve advisory wording and must not claim merge / deprecate / retire / execute already happened

## Governance-review contract

`governanceReview` is always present.

Minimum fields:
- `assetId`
- `signal`
- `evidenceMaturity`
- `inventoryEvidencePresent`
- `evidenceBasis`
- `impactPosture`
- `notes`

`evidenceMaturity` currently uses a closed three-value set:
- `prompt-only`
- `supported-signal`
- `well-evidenced`

These labels describe advisory evidence strength only; they do not imply durable governance state or lifecycle transitions.

## Control-plane contract

`controlPlane` is always present.

Minimum fields:
- `requested`
- `command`
- `mode`
- `previewRequired`
- `executionState`
- `mutationAllowed`
- `ledgerWriteAllowed`
- `selfDigestAllowed`
- `requiredCapabilities`
- `availableCapabilities`
- `missingCapabilities`
- `healthPulsePreview`
- `notes`
- `nextAction`

Rules:
- `mode` remains `shadow-advisory`
- `executionState` never claims execution happened; current shadow value is `preview-only` or `not-requested`
- `mutationAllowed`, `ledgerWriteAllowed`, and `selfDigestAllowed` remain `false`
- `healthPulsePreview` is run-scoped advisory output only, not durable ledger state
- control-plane detection only considers direct user text; protected quoted / fenced / source-tagged content must not flip `requested` to `true`
- supported command labels currently include `self-digest`, `export-ledger`, `import-ledger`, `status`, and `preview-mutation`

## Output policy contract

Minimum fields:
- `outputMode`: `explicit` | `default-cache` | `fallback-tmp`
- `cacheTtlHours`
- `managedRoot`
- `expiredRunDirsRemovedCount`
- `expiredRunDirsSample`
- `cleanupWarnings`

Rules:
- `expiredRunDirsRemovedCount` is an integer
- `expiredRunDirsSample` is a string array capped at 20 names
- `cleanupWarnings` is a string array for best-effort cleanup warnings
- `explicit` mode keeps `managedRoot = null`, `expiredRunDirsRemovedCount = 0`, `expiredRunDirsSample = []`
- Managed cache cleanup must never remove the current run directory
- Cleanup failure must not block the current run from persisting artifacts

## Structured error result

Error mode returns:
- `mode: error`
- `error`
- `actionableHints`

## Artifact emission

Always emit:
- `run_result.json`

Conditionally emit:
- companion governance YAML only when governance signal and evidence envelope are complete enough

The governance YAML is write-only run-scoped output. The repo-local minimal YAML parser is not a round-trip guarantee for block-scalar `notes`.

## Non-goals

This shadow runtime does not:
- write durable Ledger state
- mutate skills, agent config, or rules
- claim lifecycle transitions already happened
- execute dry-run or adversarial probes
- serve as the full reference implementation of the Ouro protocol
