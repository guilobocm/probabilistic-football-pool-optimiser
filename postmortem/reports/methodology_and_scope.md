# Methodology and Scope

## Decision Universe

The model projected predictions for 72 Group Stage matches. Each match had two independent predictions corresponding to two scoring rules ("pools"), generating a prospective universe of **144 decision points**.

## Scoring Rules

1. **Classic Pool**:
   - Exact score hit: 4 points
   - Correct result (win, draw, or loss): 2 points
   - Error: 0 points
2. **50-35-20 Pool**:
   - Exact score hit: 50 points
   - Correct result - Draw: 35 points
   - Correct result - Win: 20 points
   - Error: 0 points

## Evidence and Eligibility Matrix (Tiers)

Methodological validity requires that the prediction (output) was generated *before* the event occurred, based on information (*inputs*) available also before the event.

To audit this, we categorised evidence into three tiers:

- **Tier A (Full Validation)**: Independently verified outputs and inputs. Total reproducibility of the model at the time of the event.
- **Tier B (Verified Output)**: The *prediction result* (output) has irrefutable temporal proof (via an independent server) prior to the event. However, the exact inputs or code could not be independently verified. This measures accuracy but does not guarantee the absence of *data leakage* in the inputs.
- **Tier C (Local / Missing Evidence)**: Predictions based solely on local file timestamps (unverified git history, OS timestamps). Methodologically insufficient for prospective scientific validation.

## Authority and Temporality Criteria

To classify an output as Tier B, the evidence must come from an independent **timestamp authority**. 

In our case, we adopted the timestamp (message metadata) from a third-party server API (ChatGPT). The operational temporal margin adopted was:

> For temporal metadata reported by the platform, a conservative operational margin of 60 seconds was adopted (`clock_uncertainty_seconds = 60`). This value functions as a decision rule and not as a factual metrological estimate of the platform's infrastructure precision.

If the match kickoff occurred before the `evidence timestamp + 60 seconds`, the prediction for that match is **ineligible** (Tier C).

## Metric Definitions

For eligible predictions, we analysed:
- **Categorical Metrics**: 1X2 Accuracy, Exact Score Hit. Presented with Wilson Confidence Intervals (95%).
- **Regression Metrics**: Mean Absolute Error (MAE) for Goals (Team A, Team B), Scoreline L1 Error, Goal Difference MAE. Presented with Confidence Intervals (Bootstrap at 95%, 10,000 iterations).
- **Bias**: Directed error (predicted - actual) to evaluate systematic trends of under/overestimation.
- **Pool Performance**: Realised points, percentage of the maximum possible.
- **Optimisation Evaluation (Expected Points)**: The point difference (Uplift) between the suggested optimised prediction and the purely modal (highest probability) prediction.

*(Note: The calculation of MAE and Biases adopts the team ordering exactly as defined in the official FIFA schedule and maintained by the model's output dataset, hereinafter referred to as "Team A" and "Team B").*

## Dependency Treatment

Matches within the same group are not strictly independent events. Teams appear repeatedly and share the context of the group, opponents, and tournament dynamics. However, given the restricted scope of the tournament (finite sample n=71 classic), evaluation at the match level (decision-level) was selected for point estimates. The error estimates (CIs via bootstrap) assume simple random sampling with replacement (iid). The per-match bootstrap does not model this dependency structure and may underestimate uncertainty.
