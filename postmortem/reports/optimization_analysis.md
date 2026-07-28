# Optimisation Analysis (Expected Points)

The core methodological strategy of this prediction pool was not to blindly and invariably guess the most statistically "probable" scoreline (Modal), but rather the scoreline whose mathematical value in the long term would maximise the return given the prize rules (Expected Points or EP). 

This section audits whether the optimisation engine's interventions compensated for the moments when they intentionally deviated from maximum probability.

## 1. Optimisation vs. Modal Scoreline (Classic Pool)

For the 71 decisions in Cohort A, the points obtained with the optimised pick (*Expected Points Maximiser*) were compared against the points that would have been won using the purely modal pick.

**Choice Composition:**
- **Picks that differ from the Modal**: 49 (The optimisation intervened and suggested another scoreline).
- **Picks identical to the Modal**: 22 (The optimisation coincided with the obvious choice; Uplift = 0, by definition).

**Optimisation Uplift Results (Optimised - Modal):**

| Dimension | Value |
|---|---|
| Matches where the optimisation **gained** points | 19 |
| Matches where it **tied** | 40 |
| Matches where the optimisation **lost** points | 12 |
| **Total Realised Uplift (n=71)** | **+10 points** |
| Mean Realised Uplift (n=71) | +0.14 points/match |
| 95% CI for Total Uplift (Bootstrap) | [-22, +42] |

**Uplift Restricted to Divergent Picks (n=49):**

| Dimension | Value |
|---|---|
| Total Realised Uplift | +10 points |
| Mean Realised Uplift | +0.20 points/match |
| 95% CI (Bootstrap) | [-0.45, +0.86] |

> [!IMPORTANT]
> In the Tier B subset of the Group Stage, the expected points optimisation achieved a realised uplift of +10 points over the modal scoreline. The confidence interval includes zero, so the result is directional (suggesting a pragmatic benefit from optimisation) but **not statistically conclusive** at 95% significance.

## 2. Case Study: The 50-35-20 Flips (Cohort B)

At the time of submission, the author applied the optimisation metric tailored to the alternative "50-35-20" rule in four documented instances (Cohort B). 

In this pool, correctly predicting a draw awarded +35 points. The optimising intervention textually concluded that the expected value of the draw (+35) compensated for the risk of abandoning the "straight win" trend. The four predictions were deliberately substituted (flipped) to 1-1 draws.

**Paired Comparison (Evaluated under the 50-35-20 Rule):**

To measure the true decisional uplift of the flip, both the classic pick and the flip pick must be evaluated under the same target scoring rule (50-35-20).

| Match | Actual Score | Pts for Classic Pick | Pts for 50-35-20 Pick (1-1 flip) | Observed Decisional Uplift |
|---|---|---|---|---|
| South Korea vs Czechia | 2-1 | 20 pts | 0 pts | **-20 pts** |
| United States vs Turkiye | 2-3 | 0 pts | 0 pts | **0 pts** |
| Ivory Coast vs Ecuador | 1-0 | 0 pts | 0 pts | **0 pts** |
| Cape Verde vs Saudi Arabia | 0-0 | 0 pts | 35 pts | **+35 pts** |

**Total Realised Paired Uplift = +15 points**

One flip succeeded spectacularly (+35), one failed (-20), and two had no effect (both picks scored zero).

> [!WARNING]
> The four verifiable flips from the 50-35-20 pool generated an aggregate realised gain of +15 points compared to the corresponding classic decisions. Because this is an isolated and exhaustively selected sample of only four specific alterations in the conversation (non-random), **the result cannot be extrapolated to the full pool**.
