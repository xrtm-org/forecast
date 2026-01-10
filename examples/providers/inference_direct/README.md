# Direct Inference

**Script**: `run_inference_direct.py`

This example demonstrates how to use the `xrtm-forecast` inference layer directly, bypassing the graph orchestrator. This is useful for testing model connectivity or building simple scripts that need LLM access.

## Usage

```bash
# From repository root
python3 examples/providers/inference_direct/run_inference_direct.py
```

## Setup
Ensure you have set the necessary environment variables for your provider (e.g., `GEMINI_API_KEY` or `OPENAI_API_KEY`) in your `.env` file.

## Features
- **ModelFactory**: Instantiating providers via configuration.
- **Unified Interface**: Using the same `.generate()` method across different backends.
