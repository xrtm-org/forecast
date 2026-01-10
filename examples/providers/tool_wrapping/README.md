# Tool Wrapping

**Script**: `run_tool_wrapping.py`

This example shows how to wrap external Python functions or APIs into `Tool` objects that `xrtm-forecast` agents can use.

## Usage

```bash
# From repository root
python3 examples/providers/tool_wrapping/run_tool_wrapping.py
```

## Concepts
- **@tool Decorator**: Converting standard functions into agent-compatible tools.
- **Schema Generation**: Automatic JSON schema creation for LLM function calling.
- **Execution**: How the agent invokes the wrapped tool.
