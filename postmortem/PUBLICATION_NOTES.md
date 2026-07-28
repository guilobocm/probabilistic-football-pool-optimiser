# Publication Notes

The artifacts in this directory constitute the static analytical package of the 2026 World Cup Group Stage postmortem. 
This portfolio repository only contains the final validated reports, metrics, and methodology.

## Provenance
The raw datasets, external HTTP logs, and extraction scripts used to run the reproducibility pipeline remain in a private audit repository. 
The integrity of the original generation can be traced using the hashes defined in `provenance/original_private_manifest.json`.

## Scope
The scope of this publication is to demonstrate the post-event validation of the probabilistic pool optimiser's performance, as outlined in the `reports/`.

The data flow that generates these conclusions is fully deterministic. For a complete understanding of how the eligibility funnel was built and how the Tier A / Tier B limits were drawn, refer to `reports/evidence_and_eligibility.md` and `reports/limitations_and_threats_to_validity.md`.
