# Contributing to xrtm-forecast

Reference implementation for the XRTM reasoning engine. We welcome contributions!

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
- **Typing**: All new code must be fully typed.
- **Docstrings**: Use Google-style docstrings.

## Release Process
1. Update version in `pyproject.toml`.
2. Tag the release in git: `git tag -a v0.1.1 -m "Release v0.1.1"`.
3. Push tags: `git push origin v0.1.1`.
