# Backtest Workflow

**Script**: `run_backtest_workflow.py`

This example demonstrates how to run an agent through a historical simulation ("backtesting"). It uses temporal referencing to ensure the agent only has access to information available at a specific point in the past.

## Usage

```bash
# From repository root
python3 examples/kit/backtest_workflow/run_backtest_workflow.py
```

## Key Concepts
- **Temporal Sandboxing**: Restricting the agent's "Now" timestamp.
- **Historical Context**: Providing facts and search results consistent with the simulated date.
- **Evaluation**: Comparing the agent's forecast against the known historical outcome.
