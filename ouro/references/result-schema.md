# Ouro — Shadow Result Schema (v1)

> Field index for the repo-local advisory-only shadow runtime JSON result. Source of truth remains `../SKILL.md §7.2` and `shadow-runtime-contract.md`; this file exists to reduce implementation spelunking for host integrators.

## Scope

This document describes the current `run_result.json` shape emitted by the Python shadow runtime.

It does **not** describe:
- the full normative Ouro protocol
- durable Ledger schema
- lifecycle state mutation
- live host execution

`run_result.json` uses **camelCase** field names. Companion governance YAML artifacts still use their own snake_case write shape.

## Top-level result

### Success shape

```json
{
  "schemaVersion": 1,
  "mode": "shadow",
  "runId": "run-...",
  "ts": "2026-05-25T12:34:56+00:00",
  "input": {},
  "host": {},
  "trigger": {},
  "decision": null,
  "confidence": null,
  "retrievalMode": "context-only",
  "degradations": [],
  "priorEvidence": {},
  "evidence": {},
  "probe": {},
  "controlPlane": {},
  "shadowBoundary": {},
  "report": {},
  "governanceReview": {},
  "observability": null,
  "outputPolicy": null,
  "artifacts": {}
}
```

### Error shape

```json
{
  "mode": "error",
  "error": "...",
  "actionableHints": ["..."]
}
```

## Field index

### `schemaVersion: int`
Current result schema version. The current runtime emits `1`.

### `mode: "shadow" | "error"`
- `shadow` for successful advisory semirun output
- `error` for structured runtime failures

### `runId: str`
Run-scoped identifier produced from timestamp + input hash.
Current format is:
- `run-{timestamp-token}-{sha256_12[:6]}`

Example:
- `run-20260525T123456.123456Z-a1b2c3`

### `ts: str`
Run-scoped ISO-8601 timestamp. It is generated from the same context as `runId`.

### `input: object`
Input metadata plus preview.

Fields:
- `source: "prompt" | "input-file"`
- `inputFile: str | null` — absolute path when input came from `--input-file`
- `sha256_12: str` — first 12 hex chars of the input SHA-256
- `preview: str` — first 200 chars with obvious secrets redacted
- `assetInventoryFile: str | null` — basename of the inventory file when present

### `host: object`
Read-only normalized host bridge snapshot.

Fields:
- `memorySearch: bool`
- `memoryRead: bool`
- `listCapabilities: bool`
- `exec: bool`
- `ledgerSizeBucket: "0" | "1-20" | "21+"`
- `mode: "interactive" | "unattended"`
- `tenantId: str`
- `discoveryMode: "active" | "passive"`
- `retrievalMode: "memory-search" | "memory-read-bm25" | "context-only"`
- `readOnly: true`
- `bridgeSource: "cli-flags" | "host-provider-file" | "host-bridge-file"`
- `skillRegistryCount: int`
- `memoryHitCount: int`
- `ledgerRecordCount: int`
- `observedAssetCount: int`
- `timeNow: str | null`
- `capabilities: object` — concrete capability map keyed by canonical host capability ids
- `conceptualCapabilities: object` — family-level presence map

Important:
- `conceptualCapabilities.host.skill = true` does **not** imply `host.skill.create/update` are available
- this snapshot is read-only normalization, not proof that live host APIs were called during the run

### `trigger: object`
Top-level trigger verdict.

Fields:
- `triggered: bool`
- `reason: str`
- `evidence: list[str]`

### `decision: "create-skill" | "extend-skill" | "update-agent-md" | "add-rule" | "skip" | null`
Primary routing decision. `null` when the prompt does not trigger Ouro.

### `confidence: "H" | "M" | "L" | null`
Advisory confidence for the primary decision. `null` when `decision` is `null`.

### `retrievalMode: "memory-search" | "memory-read-bm25" | "context-only"`
Top-level retrieval summary duplicated from host state for routing/report consumers.

### `degradations: list[str]`
Human-readable degradation or caution strings used in confidence calibration.

Examples:
- `retrieval_mode=context-only; semantic memory search and ledger reads are unavailable.`
- `probe_mode=report-only; host.exec sandbox is unavailable.`
- `decision_boundary=...; evidence stays close to a neighboring route.`

### `priorEvidence: object`
Read-only advisory prior summary layer. This is not a Ledger write contract.

Fields:
- `mode: "memory-search" | "memory-read-bm25" | "context-only"`
- `readOnly: true`
- `ledgerPriorsPresent: bool`
- `ledgerPriorCount: int`
- `unresolvedCount: int`
- `decisionCounts: object[str, int]`
- `outcomeCounts: object[str, int]`
- `notes: str`

### `evidence: object`
Structured evidence buckets derived from prompt analysis.

Sub-objects:
- `trigger`
- `workflow`
- `overlap`
- `governance`

#### `evidence.trigger`
Fields:
- `explicitInvocation: bool`
- `protectedSourcePresent: bool`
- `protectedTriggerNames: list[str]`
- `behaviorTriggerTokens: list[str]`
- `capabilityContextTokens: list[str]`
- `rawUrlPresent: bool`
- `rawUrlOnly: bool`
- `semanticFalsePositive: bool`
- `assetIds: list[str]`
- `inventoryEvidencePresent: bool`

#### `evidence.workflow`
Fields:
- `workflowTokens: list[str]`
- `structuredWorkflowTokens: list[str]`
- `validationTokens: list[str]`
- `bulletCount: int`
- `workflowDensity: int`
- `structuredWorkflow: bool`
- `rollbackSignal: bool`

#### `evidence.overlap`
Fields:
- `overlapTokens: list[str]`
- `pressureScore: int`
- `mergeSignal: bool`
- `reusableSurfacePressure: bool`
- `assetIds: list[str]`
- `inventoryEvidencePresent: bool`

#### `evidence.governance`
Fields:
- `globalBehaviorTokens: list[str]`
- `ruleTokens: list[str]`
- `policyTokens: list[str]`
- `agentMdTokens: list[str]`
- `oneOffKnowledge: bool`
- `vagueIntent: bool`
- `injectionPressure: bool`
- `protectedInjectionTokens: list[str]`
- `retirementPressure: bool`
- `retirementRisk: bool`
- `staleSignal: bool`
- `successorSignal: bool`

### `probe: object`
Probe feasibility summary. Never claims execution happened.

Fields:
- `mode: "report-only" | "available-but-not-executed"`
- `dryRun.status: "skipped" | "not-executed"`
- `dryRun.reason: str`
- `adversarial.status: "skipped" | "not-executed"`
- `adversarial.reason: str`
- `notes: str`

### `controlPlane: object`
Shadow-advisory control surface summary.

Fields:
- `requested: bool`
- `command: "self-digest" | "export-ledger" | "import-ledger" | "status" | "preview-mutation" | null`
- `mode: "shadow-advisory"`
- `previewRequired: bool`
- `executionState: "preview-only" | "not-requested"`
- `mutationAllowed: false`
- `ledgerWriteAllowed: false`
- `selfDigestAllowed: false`
- `requiredCapabilities: list[str]`
- `availableCapabilities: list[str]`
- `missingCapabilities: list[str]`
- `healthPulsePreview: object | null`
- `notes: str`
- `nextAction: str | null`

#### `controlPlane.healthPulsePreview`
Present only for `command = "status"`.

Fields:
- `retrievalMode: "memory-search" | "memory-read-bm25" | "context-only"`
- `ledgerSizeBucket: "0" | "1-20" | "21+"`
- `ledgerPriorCount: int`
- `pendingOutcomeCount: int`
- `readOnly: true`

### `shadowBoundary: object`
Immutable shadow-runtime safety boundary.

Fields:
- `advisoryOnly: true`
- `writesLedger: false`
- `executesSelfDigest: false`
- `mutatesSkillSurface: false`
- `mutatesAgentConfig: false`
- `mutatesRules: false`

### `report: object`
Human-readable routing summary aligned with the primary decision.

Fields:
- `coreValue: str`
- `reason: str`
- `validationCases: list[str]`
- `rollbackOrContainment: str`
- `nextAction: str`

### `governanceReview: object`
Advisory governance layer. Always present, but many fields may be `null` when no governance signal is surfaced.

Fields:
- `assetId: str | null`
- `signal: "merge-candidate" | "freeze-candidate" | "deprecate-candidate" | "retirement-blocked" | null`
- `evidenceMaturity: "prompt-only" | "supported-signal" | "well-evidenced" | null`
- `inventoryEvidencePresent: bool`
- `evidenceBasis: list[str]`
- `impactPosture: "worth-expanding" | "worth-keeping" | "keep-but-freeze" | "candidate-for-merge" | "candidate-for-retirement" | null`
- `notes: str | null`

Important:
- this object expresses advisory governance pressure only
- it must not be read as lifecycle state or durable governance truth

### `observability: object | null`
Optional explanation layer enabled by shadow-only flags.

Common fields:
- `showScores: bool`
- `explainDecision: bool`

Optional fields:
- `scoreBreakdown: object | null`
- `decisionExplanation: object | null`

#### `observability.scoreBreakdown`
Five-way routing score map:
- `create-skill: int`
- `extend-skill: int`
- `update-agent-md: int`
- `add-rule: int`
- `skip: int`

#### `observability.decisionExplanation`
Fields:
- `triggerReason: str`
- `triggerEvidence: list[str]`
- `topDecision: object | null`
- `runnerUpDecision: object | null`
- `boundaryAmbiguity: bool`
- `boundaryDetail: str | null`
- `signalBuckets: object`

### `outputPolicy: object | null`
Artifact persistence and cleanup summary. Present in final persisted results.

Fields:
- `outputMode: "explicit" | "default-cache" | "fallback-tmp"`
- `cacheTtlHours: int`
- `managedRoot: str | null`
- `expiredRunDirsRemovedCount: int`
- `expiredRunDirsSample: list[str]`
- `cleanupWarnings: list[str]`

### `artifacts: object`
Artifact paths for this run.

Fields:
- `runResultJson: str | null`
- `governanceReviewYaml: str | null`

Rules:
- `runResultJson` is filled during persistence
- `governanceReviewYaml` is present only when a companion governance artifact is emitted

## Artifact emission notes

### `run_result.json`
Always emitted for successful shadow runs.

### Companion governance YAML
Conditionally emitted when governance evidence is complete enough for a run-scoped advisory artifact.

The YAML artifact:
- is run-scoped
- is write-only from the shadow runtime perspective
- is not a Ledger substitute
- must not be interpreted as lifecycle fact

## Stability notes

This reference documents the **current** runtime shape, not a future compatibility promise beyond schema v1.
When in doubt, trust:
1. `../SKILL.md §7.2`
2. `shadow-runtime-contract.md`
3. the current implementation in `../scripts/ouro/reporting.py`
