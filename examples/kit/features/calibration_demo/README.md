# Calibration Demo

**Script**: `run_calibration_demo.py`

Demonstrates techniques for measuring and improving the calibration of an agent's probabilistic forecasts. It compares an agent's stated confidence against actual outcomes (simulated or real).

## Usage

```bash
# From repository root
python3 examples/kit/features/calibration_demo/run_calibration_demo.py
```

## Concepts
- **Brier Score**: A proper scoring rule for measuring the accuracy of probabilistic predictions.
- **Reliability Diagrams**: Visualizing whether "70% confident" actually means "correct 70% of the time".
