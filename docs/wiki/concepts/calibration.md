# Reliability & Calibration (v0.2.1)

## The Philosophy: "The Researcher's Workbench"
In v0.2.1, we shifted from a narrow "Calibration Tool" to a broad **Research Platform**. We recognize that institutional researchers don't just want a Brier Score; they want the raw data to build their own custom metrics and visualizations.

## Core Concepts

### 1. The Evaluator Protocol
We decoupled metric calculation from the runner. Any class implementing `Evaluator` can be injected into the `BacktestRunner`.

```python
class Evaluator(Protocol):
    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        ...
```

### 2. Reliability Bins
Instead of forcing a Matplotlib plot on users, we calculate the raw statistical **Reliability Bins**:
- **Bin Center**: The confidence bucket (e.g., 0.95).
- **Mean Prediction**: The average confidence in that bucket.
- **Mean Ground Truth**: The actual accuracy in that bucket.
- **Count**: Sample size.

This allows users to plot ECE diagrams in their tool of choice (matplotlib, seaborn, react-vis, etc.).

### 3. Data Portability
The `EvaluationReport` now natively supports export:
- `report.to_json(path)`: Full nested structure.
- `report.to_pandas()`: Flat DataFrame for immediate analysis in Jupyter.

## Usage Pattern

```python
runner = BacktestRunner(orch)
report = await runner.run(dataset)

# Get the raw ECE Score
ece = report.summary_statistics["ece"]

# Export to Pandas
df = report.to_pandas()
df[df["tags"].str.contains("politics")].groupby("model").mean()
```
