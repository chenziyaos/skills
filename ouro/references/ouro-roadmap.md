# Ouro — Roadmap

> Design roadmap for evolving Ouro from a digestion router into a long-term capability governance engine.

## North Star

Ouro should evolve from:
- **Capability Router** → decides where new knowledge lands

toward:
- **Capability Governor** → decides what to add / merge / freeze / retire
- **Capability Auditor** → tracks whether capability changes produced durable value
- **Capability Evolution Engine** → continuously improves the capability system under safety constraints

## Phase 1 — Mature capability governance

Focus: move from "what to add" toward "how to manage the lifecycle".

Planned additions:
- Capability lifecycle states beyond create/extend: freeze / merge / deprecate / archive / retire
- Impact review: expected benefit / maintenance cost / affected scope
- Capability health pulse: not just Ledger health, but capability set health
- Conflict resolver: surface rule/config/skill collisions explicitly

## Phase 2 — AI self-improvement governance

Focus: make Ouro a governance layer for AI behavior and self-improvement.

Planned additions:
- Behavior asset taxonomy: style / safety / planning / tool-use / evaluation / memory
- Improvement funnel: observe → classify → test → route
- Meta-failure corpus: misfire / over-digestion / confidence overclaim / degradation opacity
- Dedicated prompt/eval assets for AI self-improvement scenarios

## Phase 3 — Capability operating system core

Focus: govern multi-agent capability architecture and long-term portfolio quality.

Planned additions:
- Multi-agent capability scoping
- Capability portfolio optimization
- Merge/split planning across skills
- Stronger self-governance under evaluation constraints
- Attribution and ROI tracking for capability changes

## Immediate next steps

1. Introduce a formal capability lifecycle contract
2. Add impact-oriented fields or reference concepts next to Ledger decisions
3. Expand tests from creation decisions into merge/deprecate/retire decisions
4. Separate business/process digestion from AI self-improvement digestion in evaluation assets

## Local cache vs Ledger

The repo-local `shadow_run_*` cache is an execution artifact store, not a Ledger mirror.

- Local cache keeps per-run JSON/YAML outputs for inspection, replay, and temporary comparison.
- Ledger remains the only durable decision-memory surface in the normative Ouro design.
- Cache retention and cleanup do not imply historical governance truth, outcome tracking, or durable audit state.
- Future Ledger integration should treat local cache as disposable run evidence, not as a second source of truth.
