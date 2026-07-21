# World Cup 2026 Pool Optimizer - Cryptographic Revelation

This package publicly reveals the HMAC key, canonical manifest, and two frozen artifacts associated with the pre-final commitment published before the final two matches of the 2026 World Cup.

**Publicly anchored keyed cryptographic commitment using HMAC-SHA256.**

Successful verification demonstrates that the revealed key and canonical manifest reproduce the previously published HMAC-SHA256 commitment, and that the attached artifacts match the hashes and byte lengths declared in that manifest. It does not independently prove private-code execution, causal provenance, absence of data leakage, predictive validity, or reproducibility of the private operational pipeline.

After disclosure, the HMAC key is no longer secret and anyone can compute new HMAC values with it. The evidentiary value comes from opening the commitment that was publicly anchored before the matches, not from permanent post-disclosure authenticity.

## Verification

To verify the commitment, run the included verification script:

```bash
cd reveal/world-cup-2026-pre-final
python verify_commitment.py
```

The script will:
1. Reconstruct the canonical JSON manifest.
2. Compute the HMAC-SHA256 using the revealed `precommit_key.hex`.
3. Compare the computed HMAC against the public commitment frozen in `commitments/world-cup-2026-pre-final.json`.
4. Verify the SHA-256 digests and byte sizes of the attached artifact files.

See `verification_output.txt` for an example of a successful run.

## Interpretation note

The two revealed artifacts serve different purposes.

palpites_final.md is the authoritative final-picks artifact produced by the
operational optimization pipeline. Its expected-point values are the values
associated with the submitted optimized recommendations.

montecarlo_final_10M.md is a separate sensitivity analysis based on an
independent-Poisson 90-minute simulation. Its expected-point values belong to
that simplified sensitivity model and should not be interpreted as replacements
for the values reported in palpites_final.md.

Both files are published without modification because the commitment covers
their exact original bytes.
