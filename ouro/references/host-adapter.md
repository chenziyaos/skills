# Host Adapter Contract

> **Subordinate reference.** Source of truth: `SKILL.md §10`. If any divergence exists, **§10 wins**.

Ouro is platform-agnostic. The skill body depends only on the abstract capabilities listed below.

## Capability Table (14 conceptual capabilities)

| # | Capability ID | Purpose | Degradation when missing |
|---|---|---|---|
| 1 | `host.fetch.url(url)→text` | Fetch web pages / files for Step 1 Endure | Ask user to paste content |
| 2 | `host.fetch.repo(url)→tree+files` | Fetch a repo tree + files | Per-file fetching as approximation |
| 3 | `host.fs.read/edit/write` | Local file read/write | Emit patches; user applies manually |
| 4 | `host.skill.list/create/update` | Skill registry read/write | Emit a zip + install instructions |
| 5 | `host.search(query, scope)` | Search across skills / agent md / rules | User provides candidate list |
| 6 | `host.embed(text)→vector` *(optional)* | Semantic overlap + Ledger search | Fall back to BM25 / keyword-only (not semantic top-K) |
| 7 | `host.exec(cmd, sandbox=true)` | Dry-run, adversarial probe, rollback | Emit commands; confidence -1 level |
| 8 | `host.transcribe(media)→text` *(optional)* | Video / audio transcription | Refuse media inputs |
| 9 | `host.memory.append/read/search` | **Ledger sole storage backend** | Without `host.memory.*`, durable Ledger paths are unavailable; fall back only to advisory-only / one-shot shadow mode |
| 10 | `host.time.now()` | D1/D2/D3 trigger evaluation | Infer from context timestamps; disable D1/D2 + WARN if unavailable |
| 11 | `host.list_capabilities()` *(optional)* | Active capability discovery | `discovery_mode = passive`; disable §9 main trigger 3 |
| 12 | `host.mode → "interactive"\|"unattended"` *(optional)* | Controls whether D5 activates | Default `interactive`; D5 disabled |
| 13 | `host.tenant_id → string` *(optional)* | Ledger tenant isolation | Use `'default'`; assume single-tenant |
| 14 | `host.config-manager.apply(diff)` *(optional)* | Modify hooks / permissions / env | Emit diff; user applies via native UI |

## Namespace Hierarchy

| Namespace | Purpose |
|---|---|
| `ouro.ledger` | Decision Ledger (sole storage) |
| `ouro.self-digest.pending` | D5 unattended mode: pending suggestions |
| `ouro.archive` | Archived suggestions (60-day timeout from pending) |
| `ouro.sentinel` | Memory semantic probe (per-conversation vs persistent detection) |

## Ledger Storage Contract

- Stored exclusively via `host.memory.*` under namespace `ouro.ledger`, partitioned by `tenant_id`.
- External KV / DB / FS backends are **not supported**, even if `host.fs.write` is available.
- If no memory carrier exists, Ouro refuses to run and degrades to one-shot digest mode (no compounding).

## Export / Import Dependency

- `ouro: export-ledger` depends on `host.memory.read`.
- `ouro: import-ledger` depends on `host.memory.append`.
- Without these capabilities, user must manually copy Ledger JSON.

## Shadow Runtime Bridge Snapshot

The repo-local shadow runtime now normalizes host state through a read-only bridge snapshot before routing.

### Implemented shadow subset vs normative contract

The full normative contract still lives in `SKILL.md §5`, `§7`, and `§10`. The Python runtime implements only a narrower shadow subset today.

| Area | Normative Ouro contract | Current Python shadow runtime |
|---|---|---|
| Triggering | Full eight-step protocol entry conditions | Implemented for trigger/no-trigger semirun routing |
| Routing | Five-way decision informed by Ledger + overlap + probe | Implemented as evidence-driven semirun routing |
| Governance | Advisory governance plus later lifecycle machinery | Advisory governance only; no durable lifecycle mutation |
| Host adapter | 14-capability host contract | Read-only bridge snapshot from CLI flags or `--host-bridge-file` |
| Ledger | `host.memory.*` as sole durable backend | Not implemented; runtime stays advisory-only |
| Probe | Dry-run + adversarial affect final confidence | Probe observability only; never executes |
| Output contract | Full CogniVore Report with Ledger/Health Pulse fields | Shadow JSON result contract only |

### Current bridge behavior

- Source: CLI flags (`--host-memory-search`, `--host-list-capabilities`, `--host-exec`, `--ledger-size-bucket`, `--show-scores`, `--explain-decision`, `--cache-ttl-hours`) or a structured `--host-bridge-file` JSON snapshot
- Output shape: one read-only snapshot consumed by decision routing, degradations, probe observability, and result reporting
- Shadow runtime flags that affect reporting but not host capability state:
  - `--show-scores`
  - `--explain-decision`
  - `--cache-ttl-hours`
- Current result payload includes:
  - `host.retrievalMode`
  - `host.discoveryMode`
  - `host.readOnly`
  - `host.bridgeSource`
  - `host.capabilities`
  - `host.conceptualCapabilities`
  - optional `observability.*`
  - `outputPolicy.*`
- Current limitation: bridge is advisory-only and does **not** yet call native host APIs such as `host.skill.list`, `host.memory.read/search`, or `host.time.now()`.
- Capability reporting is intentionally split into:
  - concrete keys, e.g. `host.skill.list`, `host.memory.search`
  - conceptual groups, e.g. `host.skill`, `host.memory`
  This lets the shadow runtime stay compatible with the 14-item normative contract while still exposing individually flippable bridge bits.
- `host.conceptualCapabilities` means **family-level presence only**. For example, `host.skill=true` can mean only `host.skill.list=true`; consumers must still check `host.capabilities.*` before assuming the full skill surface is available.

### Shadow boundary

- The bridge snapshot may report capability availability.
- The shadow runtime must still keep:
  - `shadowBoundary.advisoryOnly = true`
  - `shadowBoundary.writesLedger = false`
  - `shadowBoundary.mutatesSkillSurface = false`
  - `shadowBoundary.mutatesAgentConfig = false`
  - `shadowBoundary.mutatesRules = false`
- If `host.exec` is present, `probe.mode` may become `available-but-not-executed`, but the runtime must not imply that dry-run or adversarial execution actually happened.

## Binding Example

> Keys below are **host-side binding aliases**, not literal copies of the capability IDs above. Hosts may compress names to `fetch.url`, `fs`, `skill`, etc., as long as they map one-to-one to the 14 capability entries.

```yaml
host_adapter:
  fetch.url:          builtin.web_fetch
  fetch.repo:         builtin.web_fetch   # or dedicated repo tool
  fs:                 builtin.fs
  skill:              <host-skill-API>
  search:             <host-search-API or ripgrep>
  embed:              <host-embedding-API or empty>
  exec:               builtin.shell       # sandbox preferred
  transcribe:         <optional>
  memory.append:      <host-memory-write-API>
  memory.read:        <host-memory-read-API>
  memory.search:      <host-memory-search-API or empty>
  time.now:           builtin.time
  list_capabilities:  <host-capability-list-API or empty>
  mode:               "interactive"
  tenant_id:          <host-user-or-team-id>
  config-manager:     <host-config-skill>
```
