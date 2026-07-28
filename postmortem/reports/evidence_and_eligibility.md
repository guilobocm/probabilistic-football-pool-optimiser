# Evidence and Eligibility

## The Audit Story (The Prospective Funnel)

Validating predictions *ex post facto* is a data provenance challenge. The evaluation began by tracking the original artifacts.

### The Initial Census (GS-4)

The first census (`snapshot_resolution.csv`) cross-referenced the repository's local commits (`.git`) with the match schedule (kickoffs). Result: **Zero (0/144)** prospectively eligible decisions, due to the absence of local commits made in time. 

An "orphan commit" was later discovered loose in the repository's reflog, but because it was evidence supported purely by local clocks (and thus tamperable by the author), it was classified as *Tier C* (scientifically insufficient) in the **GS-4.1** erratum.

### The Search for External Evidence (GS-5)

Attention turned to cloud providers that might house authenticated timestamps (Tier B). 

1. **Gmail** search: Negative (no emails with spreadsheets sent before the World Cup).
2. **Google Drive** search: Negative (folders created after June).
3. **ChatGPT** search: Three relevant messages were located. A reference to RC v2.4 preceded the inaugural kickoff; the message containing the full CSV and the message containing the four flips were recorded after the start of the inaugural match, but before the kickoffs of the decisions that qualified.

### Authenticated Capture

A surgical capture was performed on the ChatGPT API to extract the raw JSON objects of these messages, preserving them in a manifest (`chatgpt_raw_messages_capsule.json`). This provided the `platform_reported_message_metadata` anchor, supplying external corroborated evidence of the output's existence before the respective kickoffs (limited to the security level and uptime provided by OpenAI). 

### The Final Eligibility Matrix (GS-6)

With the incorporation of native evidence from the ChatGPT server, the eligibility funnel consolidated as follows:

- **Tier A (Full Validation)**: 0 decisions
- **Tier B (Verified Output)**: 75 decisions (71 Classic, 4 Pool 50-35-20)
- **Tier C (External Evidence Missing)**: 69 decisions

The 75 Tier B decisions map to **71 unique matches** (4 matches underwent inference in both pools documented in the validated output).

The only classic match absent from this stage is **GS_A_001 (Mexico vs South Africa)**, discarded because its kickoff occurred approximately 51 minutes before the full CSV record timestamp, thus being logically disqualified.
