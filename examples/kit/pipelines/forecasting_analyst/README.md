# Forecasting Analyst Pipeline

**Script**: `pipelines/forecasting_analyst/run_forecasting_analyst.py`

A comprehensive end-to-end showcase that orchestrates a specialized `ForecastingAnalyst` agent to research and predict outcomes for a specific market question.

## Key Concepts
- **Specialist Agents**: Uses the `ForecastingAnalyst` persona.
- **Data Integration**: Connects to local market data sources (e.g., Polymarket JSONs).
- **Pipeline Orchestration**: Wraps the agent in a `GenericAnalystPipeline` for structured execution.

## Usage

```bash
# From repository root
python3 examples/kit/pipelines/forecasting_analyst/run_forecasting_analyst.py
```

## Data
This project includes a sample dataset in `data/polymarket_sample.json`, which the script uses to simulate market intelligence lookup.
