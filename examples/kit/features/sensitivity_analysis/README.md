# Sensitivity Analysis

**Script**: `run_sensitivity_analysis.py`

Shows how to perform sensitivity analysis on a forecast. By systematically varying input assumptions, the agent simulates multiple futures to understand which variables drive the outcome.

## Usage

```bash
# From repository root
python3 examples/kit/features/sensitivity_analysis/run_sensitivity_analysis.py
```

## Concepts
- **Assumption Perturbation**: Changing key variables (e.g., "Interest Rates +1%") to see the effect.
- **Robustness Check**: Determining if a forecast holds true under slightly different conditions.
