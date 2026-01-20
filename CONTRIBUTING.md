# Contributing to xrtm-forecast

Reference implementation for the XRTM reasoning engine. We welcome contributions!

## Architecture Overview

`xrtm-forecast` follows a strict three-layer architecture:

| Layer | Location | Responsibility | Key Constraint |
| :--- | :--- | :--- | :--- |
| **CORE** | `src/forecast/core/` | The "Physics" Engine — Orchestrator, State, Time, Calibration, Telemetry | **Zero Agent Logic.** Pure Python/Math. No prompts. |
| **KIT** | `src/forecast/kit/` | The "Applied" Layer — Agents, Skills, Topologies, Evaluators | **Composable.** Can import `core`, but `core` NEVER imports `kit`. |
| **PROVIDERS** | `src/forecast/providers/` | The "Hardware" — Inference (OpenAI/vLLM), Tools (Serp/Exa) | **Interchangeable.** Swappable backends. |

### The Golden Rule
> **`core` MUST NOT import from `kit` or `providers`.**

This ensures the Core remains domain-agnostic and testable without LLM dependencies.

---

## Development Environment

We provide a fully isolated development environment using **Docker** and **uv**.

### 1. Using Docker (Recommended)
```bash
# Build and start services (forecast + redis)
docker compose -f .devcontainer/docker-compose.yml up -d --build

# Enter the reasoning engine container
docker compose -f .devcontainer/docker-compose.yml exec forecast bash
```

### 2. Manual Setup (uv)
```bash
# Install uv (https://github.com/astral-sh/uv)
# Sync dependencies
uv sync --all-extras

# Run tests
uv run pytest
```

### 3. Verification Commands
```bash
uv run ruff check .      # Linting
uv run mypy .            # Type checking (strict)
uv run pytest tests/unit # Unit tests
```

---

## Key Coding Standards

### 1. Type Safety (Strict Mypy)
All code must be fully type-hinted and pass `mypy .` at project root.

### 2. License Headers
Every `.py` file must start with the Apache 2.0 license header:
```python
# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...
```

### 3. Public API (`__all__`)
Every module must define `__all__` to control the public namespace.

### 4. Docstrings (Hugging Face Style)
Use `r""" """` raw docstrings with `Args`, `Returns`, `Example` sections:

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

### 5. Terminology
Use the correct vocabulary hierarchy:
- **Stage** → **Agent** → **Skill** → **Tool**
- Use "Subject" not "Market", "Value" not "Price" in core modules

### 6. Naming Conventions
- **Modules**: `snake_case` (e.g., `calibration.py`)
- **Classes**: `PascalCase` (e.g., `BetaScaler`)
- **Examples**: Must start with `run_` (e.g., `run_causal_demo.py`)

---

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. If you've added code, add tests in the appropriate location:
   - `tests/unit/` for unit tests
   - `tests/integration/` for integration tests
   - `tests/verification/` for cross-cutting compliance tests
3. Ensure all checks pass:
   ```bash
   uv run ruff check .
   uv run mypy .
   uv run pytest tests/unit
   ```
4. Update documentation if you've added new public APIs.

---

## Agentic Engagement Rules

> These rules apply when AI agents contribute to this codebase.

1. **Sovereignty**: Agents MUST NOT commit or push changes unless explicitly instructed.
2. **Workflow Triggers**: Workflows (`/verify_and_push`, `/create_release`) MUST ONLY be triggered by the USER.

---

## Release Process

1. Update version in `src/forecast/version.py`.
2. Update `CHANGELOG.md` with new features.
3. Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push tags: `git push origin vX.Y.Z`

GitHub Actions will automatically publish to PyPI when a release is created.
