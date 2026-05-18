# Forecasting Analyst Pipeline

**Script**: `pipelines/forecasting_analyst/run_forecasting_analyst.py`

A comprehensive end-to-end showcase that orchestrates a specialized `ForecastingAnalyst` agent to research and predict outcomes for a specific market question.

## Key concepts

- **Specialist agents**: uses the `ForecastingAnalyst` persona.
- **Data integration**: connects to local market data sources (for example Polymarket JSON snapshots).
- **Pipeline orchestration**: uses `GenericAnalystPipeline` as a compatibility-named helper that assembles a forecast path for structured execution.

## Usage

```bash
python3 examples/kit/pipelines/forecasting_analyst/run_forecasting_analyst.py
```

## Data

This project includes a sample dataset in `data/polymarket_sample.json`, which the script uses to simulate market-intelligence lookup.
