# Evaluation Harness

**Script**: `run_evaluation_harness.py`

Demonstrates how to rigorously evaluate agent performance against a dataset of questions and ground truth answers. This is critical for measuring improvements or regressions in your prompts and models.

## Usage

```bash
# From repository root
python3 examples/kit/features/evaluation_harness/run_evaluation_harness.py
```

## Concepts
- **Golden Dataset**: A collection of (Question, Answer) pairs.
- **Metric Computation**: Scoring the agent's answers (e.g., via Exact Match or LLM-as-a-Judge).
- **Report Generation**: Outputting a summary of pass/fail rates.
