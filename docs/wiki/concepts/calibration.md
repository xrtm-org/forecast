# Calibration & Reliability

Calibration is the process of ensuring that probabilistic forecasts match
real-world outcomes. If a forecaster says "I am 70% confident", that event
should happen approximately 70% of the time.

## Why it matters

Large language models are frequently over-confident or inconsistently biased in
their raw probability estimates. Scoring and calibration live in **xrtm-eval**
(the in-engine scalers were removed in 0.9–0.10):

- `BrierScoreEvaluator` — Brier score with Murphy decomposition
- `ExpectedCalibrationErrorEvaluator` — ECE via reliability binning
- `LogScoreEvaluator` — negative log-likelihood
- `summarize_binary_forecasts()` — Brier + ECE + calibration curve in one call

```python
from xrtm.eval import BrierScoreEvaluator, summarize_binary_forecasts

score = BrierScoreEvaluator().score(probability=0.7, ground_truth="yes")
summary = summarize_binary_forecasts([(0.7, "yes"), (0.3, "no"), (0.9, "yes")])
print(summary["brier_score"], summary["ece"])
```

## Brier Score Decomposition

To audit the quality of a forecaster, the Brier Score is decomposed into three
components:

1. **Reliability**: How close predicted probabilities are to the true outcome
   frequency (lower is better).
2. **Resolution**: How much predictions differ from the base rate (higher is
   better).
3. **Uncertainty**: The inherent difficulty of the events being predicted.

$$ \text{Brier Score} = \text{Reliability} - \text{Resolution} + \text{Uncertainty} $$

## Reliability bins

`ReliabilityBin` (xrtm-eval) exposes mean prediction, mean ground truth, and
count so you can plot ECE diagrams in the tooling of your choice.
`EvaluationReport` exports to JSON and Pandas for notebook analysis.

## Operational signal

Every `ForecastOutput` records `parse_status` and typed `usage`, and the
analyst's `provenance.prompt_id` lets you compare calibration across prompt
versions — see [Telemetry](../../api/telemetry.md).
