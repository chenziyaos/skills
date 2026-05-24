# Changelog

## v1.1.14

- make control-plane command detection direct-text only so protected quoted, fenced, and source-tagged content stays data-only
- align shadow runtime contract docs for `priorEvidence`, `observability`, `outputPolicy`, and `evidenceMaturity`
- replace test aggregator star imports with an explicit `load_tests()` suite
- tighten asset ID inference to prefer inventory-backed identifiers and avoid file-like backticked matches
- add minimal packaging metadata and root quick-start documentation
- rename the stable CLI wrapper to `scripts/run_ouro.py` so it no longer collides with the `scripts/ouro/` package name
- drop the unused `pyproject.toml` console entry point and remove redundant `cli.py` self-alias lines to keep the repo at quasi-library skill tier

## v1.1.13

- add stable run-scoped `runId` and `ts` handling
- add `observability` and `outputPolicy` shadow-runtime contracts
- document shadow-only control-plane surface
