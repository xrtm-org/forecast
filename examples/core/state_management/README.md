# State Management

**Script**: `run_state_management.py`

This example illustrates how state flows through an `xrtm-forecast` execution graph. It focuses on `BaseGraphState`, which acts as the shared context carrier across the run.

## Usage

```bash
python3 examples/core/state_management/run_state_management.py
```

## Key concepts

- **BaseGraphState**: the shared object passed between execution-graph nodes.
- **Context updates**: how nodes append data to shared state.
- **State evolution**: how the run state changes from the first stage to the last.
