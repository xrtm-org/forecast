# Operational Scripts

This directory contains automation harnesses for the `xrtm-forecast` lifecycle.
We organize scripts by their functional domain in the CI/CD pipeline.

## Structure

### [`audit/`](audit/)
Static analysis and code quality gates. These should be run before every commit.
*   **`check_docs.py`**: Enforces license headers and docstring presence.
    *   *Usage*: `uv run python scripts/audit/check_docs.py`

### [`verify/`](verify/)
Dynamic verification and test runners. These leverage the automatic `.env` loading in `tests/conftest.py`.
*   **Standard Verification**: Run `uv run pytest tests/` to verify logic.
*   **Live Verification**: Run `uv run pytest tests/live --run-live` to verify API connectivity.

## Philosophy
We treat "Ops as Code." Manual commands are forbidden in production. All repeatable maintenance tasks must be scripted here.
