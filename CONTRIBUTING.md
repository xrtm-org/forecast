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

This repo is **local-tooling first** and uses **uv** as the primary development environment.

### 1. Preferred local setup (uv)
```bash
# Install uv (https://github.com/astral-sh/uv)
# Sync dependencies
uv sync --all-extras

# Run tests
uv run pytest
```

### 2. Optional devcontainer / Docker support

Docker support remains available for contributors who want an isolated container workflow, but it is not the primary development path.

```bash
# Build and start services (forecast + redis)
docker compose -f .devcontainer/docker-compose.yml up -d --build

# Enter the reasoning engine container
docker compose -f .devcontainer/docker-compose.yml exec forecast bash
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

Top-level packages should stay narrow:
- `xrtm.forecast`: stable orchestration and assistant entrypoints only
- `xrtm.forecast.kit`: namespace-oriented; avoid adding unrelated concrete exports at the root
- `xrtm.forecast.providers.*`: provider-facing APIs live with their provider family

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

## Cross-repo compatibility

`xrtm-forecast` sits between upstream contracts and the downstream `xrtm` product shell. Before merging a change that affects documented APIs, runtime behavior, dependency/version expectations, or cross-repo CI assumptions, follow the canonical [Cross-Repository Compatibility and Coordination Policy](https://github.com/xrtm-org/governance/blob/main/policies/cross-repo-compatibility-policy.md), [Release Readiness Policy](https://github.com/xrtm-org/governance/blob/main/policies/release-readiness-policy.md), and [Feature Status and Graduation Policy](https://github.com/xrtm-org/governance/blob/main/policies/feature-status-and-graduation-policy.md).

Coordinated changes should link sibling PRs, validate with explicit upstream/downstream refs, and avoid same-name branch aliases as the compatibility mechanism.

Treat these as stable published surfaces unless documented otherwise:

- documented `xrtm-forecast` APIs and imports
- README/install snippets and released examples
- runtime behavior or dependency floors consumed by `xrtm`

If you change one of them, record the coordination issue or PR family, note the exact upstream/downstream refs used for validation, and keep unreleased behavior out of release-pinned `xrtm` or `xrtm.org` docs until the matching package release is real.

Default `push` and `pull_request` CI validates `forecast` against explicit `main` refs for `data` and `eval`. When a coordinated PR family needs unpublished upstream changes, rerun CI with `workflow_dispatch` and set exact `data_ref` / `eval_ref` values (branch, tag, SHA, or PR ref), then record those refs in the PR description or coordination issue.

---

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. If you've added code, add tests in the appropriate location:
   - `tests/unit/` for unit tests
   - `tests/integration/` for integration tests
   - `tests/e2e/` for example-backed end-to-end flows
   - `tests/local/` for local-environment and local-LLM checks
   - `tests/verification/` for cross-cutting compliance tests
   - `tests/live/` for real-provider smoke tests
3. Match the directory with the corresponding pytest marker:

   | Layer | Directory | Marker | Typical command |
   | :--- | :--- | :--- | :--- |
   | Unit | `tests/unit/` | `unit` | `uv run pytest tests/unit -m unit` |
   | Integration | `tests/integration/` | `integration` | `uv run pytest tests/integration -m integration` |
   | Verification | `tests/verification/` | `verification` | `uv run pytest tests/verification -m verification` |
   | End-to-end | `tests/e2e/` | `e2e` | `uv run pytest tests/e2e -m e2e` |
   | Local | `tests/local/` | `local` | `uv run pytest tests/local -m local --run-local-llm` |
   | Live | `tests/live/` | `live` | `uv run pytest tests/live -m live --run-live` |
4. Ensure all checks pass:
   ```bash
   uv run ruff check .
   uv run mypy .
   uv run pytest tests/unit
   ```
5. Update documentation if you've added new public APIs.

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
