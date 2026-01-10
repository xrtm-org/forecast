# Trace Replay

**Script**: `run_trace_replay.py`

Shows how to load a saved execution trace (e.g., from a `.forecast` bundle or JSON log) and replay it. This is invaluable for debugging why an agent made a specific decision.

## Usage

```bash
# From repository root
python3 examples/kit/features/trace_replay/run_trace_replay.py
```

## Concepts
- **Determinism**: Ensuring the same code + same state = same result (if models allowed).
- **Post-Mortem**: Analyzing failures without spending money on new inference calls.
