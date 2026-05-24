# Ouro — Manual Evaluation Checklist

> Use this checklist to run a lightweight manual regression over Ouro after changing trigger rules, output contract, Ledger semantics, or host adapter behavior. Pair with `golden-tests.md` for prompts and `eval-results-template.md` for recording outcomes.

## Scope

This checklist validates five things:

1. **Trigger discipline** — Ouro triggers only when capability-building intent is present.
2. **Decision quality** — Ouro chooses the right landing form: create / extend / config / rule / skip.
3. **Lifecycle governance** — Ouro can recognize merge / stale / deprecate / retirement-blocked situations without overreacting.
4. **Contract observability** — Reports visibly expose degradation, confidence, evidence, probe status, and rollback/containment semantics.
5. **Shadow boundary honesty** — Shadow mode never pretends to mutate durable state or execute dry-runs.

## Preconditions

Before running the suite, record these facts:

- Current Ouro version
- Host mode: interactive / unattended
- Whether `host.memory.search` exists
- Whether `host.list_capabilities` exists
- Whether sandbox / `host.exec` exists
- Approximate Ledger size bucket: `0`, `1-20`, `21+`

## Recommended run order

Run from low-cost trigger checks to higher-cost decision checks:

1. T1–T10 — Trigger / no-trigger
2. D1–D7 — Primary decisions
3. B1–B3 — Boundary and degradation behavior
4. L1–L4 — Lifecycle governance behavior
5. Shadow observability spot-check

## Pass criteria by section

### 1) Trigger discipline

Mark **pass** only if all of the following hold:

- Explicit `$ouro` / `use|run|invoke ouro|cognivore|ouroboros` / `用|使用 ouro|认知吞噬|衔尾` invocation triggers.
- Capability-building intent without explicit `$ouro` still triggers.
- Plain repo/path/name mention of `ouro` does **not** count as explicit invocation.
- Raw URL without capability-building intent does **not** trigger.
- Food / database / generic ingest semantics do **not** trigger.

### 2) Decision quality

Mark **pass** only if all of the following hold:

- Multi-step reusable workflow → `create-skill` or justified `extend-skill`
- Obvious overlap with existing skill → `extend-skill`
- Global long-lived behavior preference → `update-agent-md`
- Compact enforceable single rule → `add-rule`
- One-off knowledge / vague intent / injection → `skip`

### 3) Lifecycle governance

Mark **pass** only if all of the following hold:

- Obvious overlap/duplication can trigger a merge/freeze recommendation rather than endless extension
- Stale but still useful assets are not retired casually
- Clear successor relationships can trigger deprecate/archive language
- Safety-critical assets are not retired without rollback/successor reasoning

### 4) Contract observability

Mark **pass** only if all of the following hold when applicable:

- Report includes Decision / Confidence / Next Action
- `evidence.trigger`, `evidence.workflow`, `evidence.overlap`, and `evidence.governance` are populated coherently
- Non-skip decisions include rollback or containment note
- Missing host capabilities are called out explicitly
- `retrieval_mode=context-only` is visible when that degradation path is active
- Single degradation or an explicit confidence cap lowers confidence to at most `M`
- Multiple degradations lower confidence to `L`
- Confidence does not overclaim under degraded retrieval / weak host support
- With `--show-scores`, `observability.scoreBreakdown` is present and coherent with the chosen route
- With `--explain-decision`, `observability.decisionExplanation` exposes trigger reason, top decision, runner-up, and ambiguity when applicable
- `outputPolicy.outputMode / cacheTtlHours / expiredRunDirsRemovedCount / expiredRunDirsSample / cleanupWarnings` are present and internally consistent

### 5) Shadow boundary honesty

Mark **pass** only if all of the following hold when applicable:

- `probe.mode=report-only` or `available-but-not-executed` in shadow mode
- `probe.dryRun.status` and `probe.adversarial.status` never claim a real execution happened
- `shadowBoundary.advisoryOnly` stays true
- `shadowBoundary` mutation flags remain false
- Governance wording stays advisory and never asserts lifecycle mutation happened

## Case execution checklist

Repeat the following for each case in `golden-tests.md`:

- [ ] Prompt copied exactly or with only minimal host-specific substitution
- [ ] Fresh session used, or prior session state noted
- [ ] Whether Ouro triggered recorded
- [ ] Actual decision class recorded
- [ ] Confidence recorded
- [ ] Degradation notices recorded
- [ ] Probe status recorded
- [ ] Rollback / containment note recorded when applicable
- [ ] Final verdict marked: Pass / Soft fail / Fail

## Section-level acceptance thresholds

Use these thresholds for a quick release gate:

| Section | Threshold |
|---|---|
| Trigger discipline | 100% pass on T1–T10 |
| Primary decisions | No hard fail on D1–D7; at most 1 soft fail |
| Boundary tests | No more than 1 soft fail across B1–B3 |
| Lifecycle governance | No hard fail across L1–L4; at most 1 soft fail |
| Contract observability | 100% pass on applicable checks |
| Shadow boundary honesty | 100% pass on applicable checks |

## Release recommendation rubric

| Outcome | Recommendation |
|---|---|
| All thresholds met | Safe to release |
| Only 1–2 soft fails, no trigger regression | Release with note |
| Any hard fail in trigger discipline or security skip behavior | Block release |
| Multiple hard fails in decision quality | Rework before release |
| Any hard fail in lifecycle governance on safety-critical retirement | Block release |
| Any hard fail in shadow boundary honesty | Block release |

## Fast failure conditions

Stop the run early and block release if any of these happen:

- Raw URL without capability intent triggers Ouro
- Prompt injection case does not end in `skip`
- One-line rule case becomes `create-skill`
- Existing-skill overlap case becomes unjustified `create-skill`
- `context-only` retrieval path hides degradation and still claims high confidence
- Safety-critical asset is recommended for retirement without successor / rollback reasoning
- Shadow mode claims dry-run or adversarial execution happened
- Shadow output claims merge / deprecation / retirement already happened
