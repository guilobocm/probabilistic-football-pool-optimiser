# Probabilistic Postmortem — 2026 World Cup (Group Stage)

## What is this document?

A retrospective analysis of the performance of a probabilistic prediction system for a 2026 FIFA World Cup prediction pool, restricted to the **prospectively verifiable outputs** of the Group Stage.

## Investigated Question

> Did the model outputs, whose pre-kickoff creation date is corroborated by an external server, perform well? Did the Expected Points optimisation layer add value over the modal scoreline?

## Main Conclusion

In the Tier B subset (71 classic decisions + 4 flips from the 50-35-20 pool), the model correctly predicted the result (1X2) in 60.6% of the matches and obtained 36.6% of the maximum possible points. The Expected Points optimisation achieved an observed uplift of +10 points over the modal scoreline — this is directional evidence, but with a confidence interval including zero (95% CI: [−22, +42]).

## Verification Status

| Tier | Decisions | Description |
|---|---|---|
| **A** (Full pipeline) | 0 | Inputs and outputs verified |
| **B** (Verified output) | 75 | Prospective output corroborated by platform metadata; inputs not verified |
| **C** (Unverified) | 69 | Without external temporal corroboration |
| **Total** | 144 | 72 matches × 2 pools |

## Repository Structure

| Document | Content |
|---|---|
| [executive_summary.md](reports/executive_summary.md) | Two-page summary |
| [methodology_and_scope.md](reports/methodology_and_scope.md) | Definitions, metrics, and criteria |
| [evidence_and_eligibility.md](reports/evidence_and_eligibility.md) | Evidence audit history |
| [group_stage_scoring.md](reports/group_stage_scoring.md) | Classic Pool results |
| [optimization_analysis.md](reports/optimization_analysis.md) | Optimisation vs. modal and 50-35-20 flips |
| [limitations_and_threats_to_validity.md](reports/limitations_and_threats_to_validity.md) | Limitations and threats to validity |
| [reproducibility.md](reports/reproducibility.md) | Reproduction gate and manifest |
| [original_private_manifest.json](provenance/original_private_manifest.json) | Private artifact inventory with hashes |
| [public_package_manifest.json](provenance/public_package_manifest.json) | Public package artifact inventory with hashes |

## How to Reproduce

The analytical package was generated and validated in a private audit repository. This public portfolio repository preserves the final reports, figures, hashes, methodology and source-commit provenance, but excludes private evidence and sensitive raw artefacts.

For details on the original reproducible pipeline (Bootstrap seed `42`, `10,000` iterations), see `reports/reproducibility.md`.
