# Contributing to xrtm-forecast

Reference implementation for the XRTM reasoning engine. We welcome contributions!

## Design Philosophy: "Pure Core, Practical Shell"

`xrtm-forecast` is built on a dual-layer architecture:
1.  **The Pure Core**: A strictly decoupled, domain-agnostic engine. Components (Inference, Graph, Telemetry) are pure and do not depend on global state or environment secrets directly. They are injected with explicit `Config` objects.
2.  **The Practical Shell**: Ergonomic entry points and "Assistants" that wrap the core for 80% of use cases. These high-level factories handle common configuration presets and environment variable injection automatically.

Contributors should ensure that core logic remains "Pure," while high-level APIs in `forecast.assistants` or module `__init__.py` files remain "Practical."

## Development Environment

We provide a fully isolated development environment using **Docker** and **uv**.

### 1. Using Docker (Recommended)
From the project root:
```bash
# Build and start services (forecast + redis)
docker compose -f .devcontainer/docker-compose.yml up -d --build

# Enter the reasoning engine container
docker compose -f .devcontainer/docker-compose.yml exec forecast bash
```

### 2. Manual Setup (uv)
If you prefer to run locally:
1. Install [uv](https://github.com/astral-sh/uv).
2. Sync dependencies: `uv sync --all-extras`
3. Run tests: `uv run pytest`

### 3. Workflow Commands
- **Serve Docs**: `uv run mkdocs serve`
- **Check Linting**: `uv run ruff check .`
- **Type Checking**: `uv run mypy src/forecast`

## Pull Request Process
1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes (`uv run pytest`).
4. Ensure your code passes type checking (`uv run mypy .`).
5. Make sure your code lints (`uv run ruff check .`).

## Style Guide
- **Python**: We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and use `ruff` for enforcement.
- **Typing**: All new code must be fully typed and pass `mypy` with strict settings.
- **License Headers**: Every `.py` file must start with the standard Apache 2.0 license header.
- **Docstrings**: We use an "Institutional Style" (HuggingFace/Google hybrid):
    - Use `r""" """` for all docstrings.
    - Include `Args`, `Returns`, and `Example` sections for all public classes and methods.
    - Argument types should be in backticks: ``name (`type`, *optional*, defaults to `X`): description``.
    - Include `>>>` code snippets in the `Example` section.

```python
    def example_method(self, value: int) -> bool:
        r"""
        Brief description of what the method does.

        Args:
            value (`int`):
                Detailed description of the argument.
        
        Returns:
            `bool`: Description of the return value.

        Example:
            ```python
            >>> obj.example_method(42)
            True
            ```
        """
```


## Naming Conventions
- **Modules**: `snake_case` (e.g., `utils.py`).
- **Classes**: `PascalCase` (e.g., `AgentFactory`).
- **Scripts**: Runnable scripts (especially examples) must start with `run_` (e.g., `run_glue.py`).

## Agentic Engagement Rules
1. **Sovereignty**: The Agent MUST NOT commit or push changes unless explicitly instructed by the USER.
2. **Workflow Triggers**: Workflows (e.g. `/verify_and_push`, `/create_release`) MUST ONLY be triggered by the USER. Proactive execution by the Agent is strictly prohibited.

## Release Process
1. Update version in `src/forecast/version.py`.
2. Tag the release in git: `git tag -a v0.2.1 -m "Release v0.2.1"`.
3. Push tags: `git push origin v0.2.1`.
