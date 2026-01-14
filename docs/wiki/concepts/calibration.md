# Calibration & Reliability (v0.3.1)

Calibration is the process of ensuring that an agent's probabilistic forecasts match real-world outcomes. If an agent says "I am 70% confident," that event should happen exactly 70% of the time.

## The Problem: LLM Over/Under-confidence

Large Language Models (LLM) are notorious for being over-confident or inconsistently biased in their raw probability estimates. Without calibration, these probabilities are "unreliable" for institutional decision-making.

## The Solution: Platt Scaling

`xrtm-forecast` implements **Platt Scaling** (via the `PlattScaler` class) to correct these biases. 

### How it Works
Platt Scaling fits a logistic regression model to the agent's raw probability outputs ($P_{raw}$) against the actual binary outcomes ($y$). 

$$ P(y=1 | P_{raw}) = \frac{1}{1 + \exp(A \cdot P_{raw} + B)} $$

The parameters $A$ and $B$ are learned from historical data (calibration set), allowing the system to "stretch" or "compress" the LLM's confidence into a mathematically rigorous probability.

## Brier Score Decomposition

To audit the quality of a forecaster, we use the **Brier Score**, which we decompose into three components:

1. **Reliability**: How close the predicted probabilities are to the true frequency of outcomes. (Lower is better).
2. **Resolution**: How much the predictions differ from the base rate (average frequency). (Higher is better).
3. **Uncertainty**: The inherent difficulty of the events being predicted.

$$ \text{Brier Score} = \text{Reliability} - \text{Resolution} + \text{Uncertainty} $$

## The Researcher's Workbench

### 1. The Evaluator Protocol
We decouple metric calculation from the runner. Any class implementing `Evaluator` can be injected into the `BacktestRunner`.

### 2. Reliability Bins
We calculate raw statistical Reliability Bins (Mean Prediction, Mean Ground Truth, Count) to allow users to plot ECE diagrams in their tool of choice (matplotlib, seaborn, etc.).

### 3. Data Portability
The `EvaluationReport` natively supports export to JSON and Pandas for immediate analysis in Jupyter notebooks.
