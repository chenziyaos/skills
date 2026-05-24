# Decision Ledger — Schema & Contract

> Subordinate reference. Source of truth: `SKILL.md §5`. This file is an English summary; if any field, threshold, or capacity number diverges from §5, **§5 wins**.

The Decision Ledger is Ouro's append-only memory of every digestion decision (including failures). It is the substrate of M2/M3 compounding.

## Storage

- Backend: `host.memory.*`, namespace `ouro.ledger`, partitioned by `tenant_id`.
- No external KV / DB / FS. The ledger's lifecycle is bound to the host's memory lifecycle.
- If no memory carrier exists → Ouro degrades to one-shot digest mode (no compounding).

## Record Shape (schema_version: 1.2)

```json
{
  "schema_version": "1.2",
  "id": "<uuid>",
  "ts": "<ISO-8601>",
  "tenant_id": "<host.tenant_id or 'default'>",
  "input": {
    "type": "repo|article|doc-site|snippet|skill|agent-md|media|structured|self",
    "uri": "<url or hash>",
    "sha256_12": "<first 12 hex chars of sha256>",
    "summary": "<<=200 chars>"
  },
  "analysis": {
    "core_value": "<one sentence>",
    "shape": "knowledge|process|tool|style|hybrid",
    "stability_months": 12,
    "risk_surface": "low|mid|high",
    "falsifiability_cases": 2
  },
  "scan": {
    "top_overlap": [{"target": "<skill/path>", "score": 0.86, "method": "embedding|keyword-only"}],
    "conflicts": [{"target": "<...>", "kind": "rule|trigger|scope"}]
  },
  "decision": "create-skill|extend-skill|update-agent-md|add-rule|skip",
  "target": "<concrete landing point>",
  "probe": {
    "dry_run": "pass|fail|skipped",
    "adversarial_pass_rate": 0.85,
    "perf_overhead_ms": 0,
    "budget_used": {"tokens": 2048, "wall_ms": 12000, "cost_usd": 0.02}
  },
  "confidence_provisional": "H|M|L",
  "confidence_final": "H|M|L",
  "outcome": "pending|success|reverted|regret",
  "outcome_ts": "<ISO-8601 or null>",
  "outcome_window_days": 7,
  "stale": false,
  "reviewer": "<user identifier>",
  "inspiration_lineage": "<optional metaphor lineage, e.g. '无脸男 → Ouroboros'>",
  "notes": "<optional free text>"
}
```

## Write Semantics

- **Append-only.** Existing records are never deleted; outcomes are updated in place.
- **Dedup key:** `(input.sha256_12, decision, target)`. A re-digest of the same triple updates `outcome` / `notes` / `probe` rather than appending.
- **Two-phase commit:** Phase 1 writes `outcome=pending` *before* the actual mutation; Phase 2 performs the mutation; Phase 3 transitions outcome (`pending → success` after Step 5.5 patrol, or `pending → reverted` on failure).

## Query Semantics

- With `host.memory.search` → semantic top-K retrieval.
- With only `host.memory.read` → full dump + BM25/keyword sort (not semantic top-K).
- With only conversation context → Ledger summary in system/context for base model self-retrieval.

## Success Definition (by target type)

| target type | "used at least once" criterion |
|---|---|
| create-skill / extend-skill | Skill invoked ≥1 time by user or another skill |
| update-agent-md | Modified behavior triggered ≥1 time in subsequent sessions |
| add-rule | Rule matched/fired ≥1 time |

## Outcome Lifecycle

| Transition | Trigger |
|---|---|
| `pending → success` | ≥7 days after Evolve, no rollback, target capability used at least once (see table above) |
| `pending → reverted` | User rolls back within outcome window (default 7 days), or Phase 2 execution failed |
| `success → regret` | A later digestion supersedes the decision, or the target is deprecated within 6 months |
| `* → stale=true` | Half-life elapsed (TTL patrol in Step 5.5); record kept, weight halved |

## Capacity Policy

| Threshold | Action |
|---|---|
| > 200 entries | Compress oldest 50 successful entries into a single aggregate summary (keep statistical metrics) |
| > 400 entries | Compress reverted/regret entries (keep id + summary + decision + outcome; drop probe details) |
| > 600 entries | Refuse new writes; force a self-digest |

`reverted` and `regret` records are **never deleted** — only compressed. Failure semantics are preserved forever.

## Failure Corpus

The subset where `outcome ∈ {reverted, regret}`. Step 4 must query it before recommending; an unavailable Failure Corpus downgrades confidence by one level and is annotated in the *Risk* section.

## Cross-Host Migration

The ledger does not migrate automatically across hosts. Two commands are provided:

- `ouro: export-ledger` — calls `host.memory.read(namespace="ouro.ledger")`, outputs JSON to user.
- `ouro: import-ledger <json>` — calls `host.memory.append` with dedup into the current namespace.

**Implementation dependency**: Both commands require `host.memory.read/append`. Without these capabilities, user must manually copy Ledger JSON.
