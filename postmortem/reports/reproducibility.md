# Reproducibility and Artefact Manifest

The Group Stage data flow was structured into a deterministic reproducible pipeline to attest all tables and analyses documented in this postmortem.

The analytical package was generated and validated in a private audit repository. This public portfolio repository preserves the final reports, figures, hashes, methodology and source-commit provenance, but excludes private evidence and sensitive raw artefacts.

## Manifest and Integrity

The provenance and SHA-256 hashes of all output artefacts derived from the original private pipeline are preserved in `postmortem/provenance/original_private_manifest.json`.

A dedicated manifest for this public repository is available at `postmortem/provenance/public_package_manifest.json`, ensuring the integrity of the published static reports.

## Testing Scope

All six existing tests passed, confirming the stability of the base internal scoring logic. Additionally, a smoke test validates the public entry point and the schema of the three output samples. The schemas and internal logic are NOT comprehensively validated beyond these checks.
