# State Management

**Script**: `run_state_management.py`

This example illustrates how state flows through the `xrtm-forecast` graph. It focuses on the `BaseGraphState` object, which acts as the "context carrier" across all nodes in a reasoning chain.

## Usage

```bash
# From repository root
python3 examples/core/state_management/run_state_management.py
```

## Key Concepts
- **BaseGraphState**: The immutable-style object passed between nodes.
- **Context Updates**: How nodes append data to the shared state.
- **State Evolution**: Observing how the state changes from the first node to the last.
