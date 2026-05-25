# Ouro

Ouro is a meta-skill for turning reusable workflows, policies, and capability signals into durable agent surfaces. This repository currently ships an advisory-only Python shadow runtime for semirun validation; it does not write ledger state or mutate skills, rules, or agent config.

## What is in this repo

- `SKILL.md` — primary skill contract
- `references/` — focused protocol and runtime references
- `scripts/run_ouro.py` — stable CLI entrypoint for the shadow runtime
- `scripts/ouro/__main__.py` — package entrypoint for `python3 -m ouro`
- `scripts/ouro/` — runtime package implementation
- `scripts/tests/` — modular unittest suite

## Quick start

Requirements:

- Python 3.10+

Run the CLI help:

```bash
python3 -m ouro --help
```

The stable wrapper remains available too:

```bash
python3 scripts/run_ouro.py --help
```

Run the main test suite:

```bash
python3 -m unittest discover -s scripts -p 'test_ouro.py'
```

Run the modular suites directly:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

## Runtime boundary

The repo-local runtime is intentionally shadow-only:

- advisory-only outputs
- no durable ledger writes
- no self-digest execution
- no skill, rule, or agent-config mutation
- governance artifacts are run-scoped write-only outputs

For the detailed protocol and current shadow contract, start with:

- `SKILL.md`
- `references/shadow-runtime-contract.md`
