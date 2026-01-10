# Tiered Reasoning

**Script**: `run_tiered_reasoning.py`

Demonstrates a "Fast and Slow" thinking pattern. The system first tries a cheap, fast model. If confidence is low, it escalates to a more capable (and expensive) reasoning model.

## Usage

```bash
# From repository root
python3 examples/kit/features/tiered_reasoning/run_tiered_reasoning.py
```

## Concepts
- **Model Cascading**: optimizing for cost/latency by default, and quality only when needed.
- **Confidence Gates**: Using self-evaluating metrics to trigger escalation.
