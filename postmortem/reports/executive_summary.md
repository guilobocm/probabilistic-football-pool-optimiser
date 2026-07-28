# Executive Summary

## Context

A probabilistic system was built to generate optimised predictions for a 72-match FIFA World Cup 2026 Group Stage prediction pool. The system operated under two distinct scoring rules (Classic Pool and 50-35-20 Pool), producing 144 prospective decisions.

## How many decisions were auditable?

Of the 144 decisions, **75** have outputs whose pre-kickoff creation date is corroborated by metadata from the ChatGPT platform server (Tier B). Zero decisions have full verification of both inputs and outputs (Tier A). The remaining 69 lack external temporal corroboration (Tier C).

The 75 Tier B decisions map to **71 unique matches**: 71 from the Classic Pool and 4 from the 50-35-20 Pool (these four were explicit alterations documented in the conversation).

## What did the model get right?

**Classic Pool Cohort (n = 71):**

| Metric | Value | 95% CI |
|---|---|---|
| Categorical Hit (1X2) | 60.6% | [48.9%, 71.1%] |
| Exact Score Hit | 12.7% | [6.8%, 22.4%] |
| Realised Points | 104 / 284 (36.6%) | — |
| Mean Points per Match | 1.46 | [1.15, 1.77] |

The model consistently underestimated the total goals observed (bias = −1.61 goals/match).

## Did the optimisation add value?

Of the 71 classic matches, 49 had an optimised pick that differed from the modal scoreline. The optimisation achieved a **realised uplift of +10 points** over the modal scoreline.

- 19 matches where the optimisation gained points
- 40 matches where it tied
- 12 matches where it lost points

95% CI for total uplift: **[−22, +42]**. The evidence is directional — favouring the optimisation — but insufficient to reject the null hypothesis at the 5% level.

## The four 50-35-20 flips

In the four documented cases, maximising Expected Points under the asymmetric rule converted straight wins into draws. Evaluated under the 50-35-20 rule, two flips failed (−20 pts each compared to the classic pick) and two correctly predicted 0-0 draws, activating the 35-point premium (+35 pts each compared to the classic pick). Net realised decisional uplift: **+30 points**. This result cannot be extrapolated to the full pool.

## Which claims remain prohibited?

1. Full validation of the pipeline (Tier A is empty).
2. Exclusion of data leakage in the inputs.
3. Representative evaluation of the 50-35-20 pool (only 4 of 72 decisions verified).
4. Calculation of Log Loss, RPS, or Brier 1X2 (probabilistic distribution not preserved).
5. Generalisation to other World Cups.
6. Claims of perfect probabilistic calibration of the model.

## Decisive Limitations

- The **inputs** (market odds) were not preserved with temporal certification. The root cause of the underestimation bias remains undetermined.
- The **complete probabilistic distribution** is missing from the verified outputs, precluding cross-entropy metrics.
- The **full raw server response** (HAR) was not initially preserved. A derived and targeted capsule was extracted subsequently from the platform's authenticated response.
- The sample size of **71 matches** limits statistical power. Plausible differences may fail to reach conventional significance.
