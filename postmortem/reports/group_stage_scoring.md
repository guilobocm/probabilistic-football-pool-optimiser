# Group Stage Scoring (Classic Pool)

> The following results refer to **Cohort A** (n = 71), which are the Classic Pool decisions with prospectively confirmed outputs (Tier B). 

## 1. Categorical Hit Metrics

| Metric | Observed Performance | 95% Confidence Interval (Wilson) |
|---|---|---|
| Categorical Hit (1X2) | **60.6%** (43 hits) | [48.9%, 71.1%] |
| Exact Score Hit | **12.7%** (9 hits) | [6.8%, 22.4%] |

## 2. Absolute Residual Metrics (Regression)

Analysis of the error in predicting the exact number of goals:

| Metric | Mean Error | 95% CI (Bootstrap) |
|---|---|---|
| MAE Team A | **1.37 goals** | [1.08, 1.66] |
| MAE Team B | **0.77 goals** | [0.61, 0.94] |
| Scoreline Total MAE (L1) | **2.14 goals** | [1.82, 2.48] |
| Goal Difference MAE | **1.32 goals** | [1.07, 1.61] |

## 3. Directionality and Biases

The model systematically predicted fewer goals than reality (Bias = `Predicted - Actual`). The tournament proved to be quite offensive.

| Dimension | Team A | Team B |
|---|---|---|
| Actual Goals (Mean) | 2.07 | 0.87 |
| Predicted Goals (Mean) | 0.99 | 0.35 |
| **Bias** | **-1.08** | **-0.52** |

The **Total Goals Bias was -1.61 goals/match**. The asymmetry of the MAE (1.37 vs 0.77) is compatible with the difference observed in the goal distribution between Team A and Team B. The audit found no mapping error, although the size of the errors also depends on the distribution of the predictions and individual residuals.

## 4. Pool Matrix Return

In the classic scoring (Exact=4, 1X2=2), the model performed as follows:

| Metric | Value |
|---|---|
| Realised points | **104 points** |
| Maximum possible points | 284 points |
| Yield (Pct of Max) | **36.6%** |
| Mean points per match | 1.46 (95% CI: [1.15, 1.77]) |

## 5. Expected Points (EP) - Aggregate Realisation Ratio

When choosing the optimised picks, the model predicted an **Expected Points (EP)** value for each match. We evaluated how well this promise translated into reality.

| Dimension | Value |
|---|---|
| Total Projected EP | 108.94 points |
| Total Realised Points | 104.00 points |
| Aggregate Gap | -4.94 points |
| **Aggregate Realisation Ratio** | **0.955** (95.5%) |
| Gap 95% CI (Bootstrap) | [-26.2, +16.7] |

> [!NOTE]
> The realised points corresponded to 95.5% of the sum of the expected points. The bootstrap interval of the aggregate gap includes zero, indicating no detectable aggregate bias in the realisation of expected points in this sample. This does not constitute a complete evaluation of probabilistic calibration.
