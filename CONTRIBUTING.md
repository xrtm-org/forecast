# Contributing to xrtm-forecast

`xrtm-forecast` owns the forecasting runtime: providers, orchestration, runtime APIs, and code-first examples. If you still need the released product-first workflow, start in [`xrtm`](https://github.com/xrtm-org/xrtm) and come here once you are working directly on the runtime.

## Start with the right repo

| If you are changing... | Start here | Why |
| --- | --- | --- |
| runtime APIs, provider integrations, orchestration internals, or library examples | `forecast` | this repo owns the runtime implementation |
| released CLI/product docs, canonical run artifacts, or provider-free first-success flow | [`xrtm`](https://github.com/xrtm-org/xrtm) | the product shell owns the public workflow |
| public site navigation or newcomer-facing mirrors of released behavior | [`xrtm.org`](https://github.com/xrtm-org/xrtm.org) | the site presents accepted product/governance truth |
| schemas, compatibility rules, or org-wide contributor policy | [`governance`](https://github.com/xrtm-org/governance) | shared standards live there |

## Local setup

In the standard sibling-checkout workspace, use the bootstrap script:

```bash
./scripts/setup_dev.sh
```

If you are working on this repo by itself, the minimal local setup is:

```bash
uv sync --all-extras
```

## Standard checks

Run the normal gate before opening a PR:

```bash
uv run python scripts/audit/check_docs.py
uv run ruff check .
uv run mypy .
uv run pytest tests/unit
```

Use deeper checks when your change reaches beyond unit-scope behavior:

```bash
uv run pytest tests/integration
uv run pytest tests/verification
uv run pytest tests/live --run-live
```

## Where docs, tests, and policy belong

- **`forecast`**: runtime/library docs, code examples, provider behavior, and unit/integration/runtime tests.
- **`xrtm`**: released CLI story, canonical run-artifact behavior, and product-level user flows.
- **`xrtm.org`**: newcomer-facing navigation and mirrors of accepted released behavior.
- **`governance`**: Forecast Object schemas, compatibility rules, and contributor/review policy.

Use the repo test directories intentionally:

- `tests/unit` for default runtime coverage and CI-safe checks
- `tests/integration` / `tests/verification` when the change crosses component boundaries
- `tests/live` only when you are intentionally validating real provider connectivity

Do not move branch-only runtime conveniences into release-pinned `xrtm` or `xrtm.org` docs until the package release, downstream docs, and validation evidence move together.

## PR expectations

1. Branch from `main`.
2. Keep examples and tests close to the runtime surface you changed.
3. When a stable surface changes, note downstream follow-up for `xrtm` and `xrtm.org`.
4. Use explicit upstream/downstream refs for coordinated validation rather than same-name branch assumptions.
5. Include the commands you ran in the PR description.

## Related references

- [ARCHITECTURE.md](ARCHITECTURE.md) for the runtime/layer split
- [AGENTS.md](AGENTS.md) for repo-specific engineering guardrails
- [`governance` cross-repo policies](https://github.com/xrtm-org/governance/tree/main/policies) when the change affects stable shared surfaces
