## Summary

Unifies the public repository’s CI and resolves the operational debts uncovered during the portfolio migration.

## Changes

- removes the obsolete `Portfolio quality` workflow and consolidates all checks into `ci.yml`;
- resolves Ruff import-order and unused-import failures;
- adds an isolated CLI contract to `src.pipeline.run_all`;
- prevents the smoke test from writing to repository outputs, invoking live odds ingestion, or running 100,000 simulations;
- restores multilingual team aliases while excluding alias data structurally from the public-language audit;
- synchronises `requirements.txt` with the locked `uv` environment;
- adds deterministic verification of the public postmortem manifest;
- aligns `scripts/validate.sh` with the unified GitHub Actions workflow.

## Validation

The following checks pass locally:

```bash
bash scripts/validate.sh
```

This includes:

- locked dependency synchronisation;
- Ruff lint and formatting;
- public-language audit;
- public-package manifest verification;
- pytest, including isolated smoke and language-gate tests;
- mypy;
- the synthetic tournament demo;
- clean-working-tree verification.

## Scope

These changes do not alter the football model, scoring rules, optimisation mathematics, or tournament simulation logic. They improve execution isolation, compatibility, dependency reproducibility, provenance verification, and CI governance.

## Repository settings

Before requiring the unified CI check, remove the obsolete required status:

`Portfolio quality / test-and-language-audit`

The new required check should be the `test` job from the unified `CI` workflow.
