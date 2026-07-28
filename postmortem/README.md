# Probabilistic Postmortem — FIFA World Cup 2026 Group Stage

## Purpose

This report evaluates a probabilistic prediction system for a FIFA World Cup 2026 pool, restricted to outputs whose existence before the relevant kick-off could be corroborated through external platform metadata.

## Questions investigated

> How well did the prospectively corroborated outputs perform? Did expected-points optimisation add realised value relative to selecting the modal scoreline?

## Main conclusion

Within the Tier B subset, the 71 Classic Pool decisions achieved **60.6% 1X2 accuracy** and **36.6% of the maximum available points**. Expected-points optimisation produced an observed **+10-point uplift** relative to the modal scoreline, but the 95% bootstrap interval **[-22, +42]** includes zero. The evidence is directionally favourable, not statistically conclusive.

## Verification status

| Tier | Decisions | Description |
|---|---:|---|
| **A — complete pipeline** | 0 | Inputs, outputs, and their binding independently verified |
| **B — output corroborated** | 75 | Prospective output corroborated by platform metadata; inputs not independently verified |
| **C — insufficient prospective evidence** | 69 | No sufficient external temporal corroboration |
| **Total** | 144 | 72 matches across two pool rules |

The 75 Tier B decisions correspond to **71 unique matches**: 71 Classic Pool decisions and four documented 50-35-20 decisions.

## Report structure

| Document | Contents |
|---|---|
| [Executive summary](reports/executive_summary.md) | Results and decision-relevant conclusions |
| [Methodology and scope](reports/methodology_and_scope.md) | Definitions, metrics, and evidence criteria |
| [Evidence and eligibility](reports/evidence_and_eligibility.md) | Temporal provenance audit |
| [Group-stage scoring](reports/group_stage_scoring.md) | Classic Pool results |
| [Optimisation analysis](reports/optimization_analysis.md) | Optimised picks versus modal scorelines and four documented flips |
| [Limitations and threats to validity](reports/limitations_and_threats_to_validity.md) | Claims the evidence does and does not support |
| [Reproducibility](reports/reproducibility.md) | Public reproduction boundary and source manifests |
| [Original private manifest](provenance/original_private_manifest.json) | Historical private artefact inventory with hashes |
| [Public package manifest](provenance/public_package_manifest.json) | Published package inventory with hashes |

## Reproduction boundary

The analytical package was generated and validated in a private audit repository. This portfolio repository preserves the final reports, figures, hashes, methodology, and source-commit provenance while excluding private evidence and sensitive raw artefacts.

For deterministic parameters and the public reproduction boundary, see [reproducibility.md](reports/reproducibility.md).

## Naming convention

Human-facing prose follows standard New Zealand English. A small number of historical filenames and schema identifiers retain their original spelling so that hashes, provenance links, and automation remain stable.
