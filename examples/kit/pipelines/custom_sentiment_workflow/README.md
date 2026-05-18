# Custom Sentiment Workflow

**Script**: `run_custom_sentiment_workflow.py`

This example keeps its legacy directory name for compatibility, but the code demonstrates a custom execution graph for aggregate sentiment analysis.

## Usage

```bash
python3 examples/kit/pipelines/custom_sentiment_workflow/run_custom_sentiment_workflow.py
```

## Concepts

- **Map-reduce**: process many inputs and summarize them.
- **Custom execution graph**: combine sentiment, aggregation, and reporting stages inside one forecast path.
- **Specialized prompting**: use focused prompts for analytical tasks such as sentiment extraction.
