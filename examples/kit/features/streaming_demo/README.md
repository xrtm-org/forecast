# Streaming Demo

**Script**: `run_streaming_demo.py`

Demonstrates how to handle streaming responses from the agent. This is essential for building responsive user interfaces where tokens act as a "typewriter" effect.

## Usage

```bash
# From repository root
python3 examples/kit/features/streaming_demo/run_streaming_demo.py
```

## Concepts
- **Async Generators**: Consuming token streams in real-time.
- **UI Responsiveness**: Providing immediate feedback to the user before the full thought is complete.
