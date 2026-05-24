# Ouro — Capability Lifecycle (Draft)

> Draft lifecycle model for capability assets governed by Ouro.
>
> This document describes future host-side governance semantics. It is out of scope for the current repo-local Python shadow runtime and must not be treated as its machine contract.

## Asset types

- Skill
- Agent-md configuration
- Rule
- Prompt / evaluation asset

## Lifecycle states

| State | Meaning |
|---|---|
| `proposed` | Identified by Rewrite Plan but not executed |
| `active` | In use and within outcome window / healthy period |
| `stale` | Still present but aging / weakly evidenced |
| `frozen` | No new growth; kept for compatibility / audit |
| `merged` | Semantics absorbed into another asset |
| `deprecated` | Still present but should no longer be extended |
| `archived` | Retained for audit only |
| `retired` | Operationally removed from active capability set |

## Core transitions

- `proposed -> active`: Step 5 executed and outcome enters pending/success path
- `active -> stale`: low use or TTL aging
- `active -> frozen`: intentionally stop evolving but keep using
- `active -> merged`: absorbed into another asset due to high overlap
- `active -> deprecated`: should no longer be extended; replacement exists
- `deprecated -> archived`: kept only for audit / migration history
- `archived -> retired`: removed from active capability set, retained only in records

## Governance questions before retirement

Before freezing / merging / deprecating / retiring, Ouro should ask:

1. What active behaviors depend on this asset?
2. Is there a successor asset?
3. Can the change be rolled back?
4. Is the asset low-value, low-use, or redundant?
5. Does retirement reduce complexity more than it increases risk?

## Evaluation hooks

Future runtime validation should include cases for:
- obvious merge candidates
- stale but still useful assets
- deprecated but not yet retired assets
- retirement recommendations that should be blocked for safety
