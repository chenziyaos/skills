# Ouro — Shadow Target Selection (Draft)

> Comparative analysis of the first real write target for `governance_review` shadow persistence.

## Goal

Choose the safest first runtime location for governance shadow writes before any Ledger-adjacent persistence is attempted.

The candidates are:
1. run-scoped result artifact
2. host-side review note
3. host-memory shadow namespace

## Evaluation criteria

The comparison below focuses on:
- reversibility
- risk of being mistaken for authoritative fact
- support for later audit/comparison
- coupling risk with Ledger or primary decision semantics
- implementation complexity

## Candidate A — Run-scoped result artifact

### Description
A governance shadow record is written only into a per-run artifact or result file.

### Advantages
- Lowest blast radius
- Easy to inspect and discard
- Naturally tied to a specific run
- Does not pretend to be long-term system memory
- Best fit for early advisory-only rollout

### Weaknesses
- Cross-run comparison requires extra aggregation later
- Governance memory is fragmented across artifacts
- Easy to underuse if no aggregation discipline emerges

### Main risks
- Weak signal repetition may later be over-read as consensus if aggregated carelessly
- Users may assume artifact-level records are more durable than they are

### Coupling risk
- Lowest coupling with Ledger
- Very low risk of corrupting primary decision semantics

### Recommended use
Best first write target when the protocol is still stabilizing.

## Candidate B — Host-side review note

### Description
A governance shadow record is stored as a host-visible note/review object, separate from the core Ledger.

### Advantages
- More durable than a run artifact
- Easier to audit across runs than loose files
- Can still remain conceptually separate from primary decision records

### Weaknesses
- More likely to be mistaken for approved governance truth
- Depends on host UX and semantics
- Requires stronger discipline around note vs fact boundaries

### Main risks
- Review notes may be read by humans/tools as “approved governance actions” rather than advisory observations
- Host-specific note semantics may vary and blur authority level

### Coupling risk
- Medium coupling: still outside core Ledger, but much closer to system memory
- Risk rises if hosts later treat notes as operational truth

### Recommended use
Good second target once report/eval/runtime conventions are stable.

## Candidate C — Host-memory shadow namespace

### Description
A governance shadow record is written into host memory under a dedicated shadow namespace.

### Advantages
- Best continuity across runs
- Strongest base for future audit and promotion analysis
- Most natural precursor to Ledger-adjacent persistence

### Weaknesses
- Highest risk of being mistaken for durable fact
- Requires explicit namespace and retention discipline
- Strongest temptation to skip directly toward schema-like behavior

### Main risks
- Advisory candidate signals become “memory facts” too early
- Weak evidence may be repeatedly resurfaced and amplified by later reasoning
- Namespace-level accumulation can create false consensus if aggregation rules are immature

### Coupling risk
- Highest coupling short of direct Ledger writes
- Strongest risk of semantic bleed into decision/outcome history

### Recommended use
Only after governance signals, evidence fields, and inventory-aware reasoning are stable under runtime validation.

## Recommended ranking

### 1. Run-scoped result artifact (recommended first)
Why:
- safest
- easiest to reverse
- easiest to reason about as non-authoritative
- aligns with advisory-only rollout

### 2. Host-side review note
Why:
- useful once repeated runtime runs show stable signals
- still separable from core Ledger if note semantics are controlled

### 3. Host-memory shadow namespace
Why:
- powerful, but easiest to over-trust too early
- should only come after shadow semantics and aggregation discipline are proven

## Selection rule of thumb

Use candidate A when:
- you are still stabilizing protocol semantics
- you want low-risk observation and comparison

Use candidate B when:
- the host has a clear note/review abstraction separate from facts
- teams need durable human-readable audit trails

Use candidate C when:
- governance signals are already stable across multiple runs
- evidence maturity is consistently recorded
- inventory-aware cases routinely outperform prompt-only cases
- the host can isolate shadow memory from authoritative records

## Current recommendation for Ouro

Given the current state of Ouro:
- governance signals have only recently entered the main report contract
- impact reasoning is still at evaluation/runtime maturity
- capability inventory is still a draft
- aggregation discipline is newly defined

The recommended first real write target is:

> **run-scoped result artifact**

Everything else should be treated as a later-stage rollout target.
