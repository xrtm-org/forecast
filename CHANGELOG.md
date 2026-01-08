# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-01-08

### Fixed
- **CI Stability**: Resolved a unit test failure in `test_factory_profiles.py` caused by missing environment API keys.

## [0.1.3] - 2026-01-08

### Added
- **Local Model Sovereignty**: Introduced `HuggingFaceProvider` for local, air-gapped reasoning via state-of-the-art weights (LLama-3, Mistral, etc.).
- **Tiered Reasoning (RoutingAgent)**: Added a composite `RoutingAgent` that dispatches tasks between high-cost smart models and low-cost fast/local models.
- **Institutional Data Skills**: Added `SQLSkill` (SQLite/Postgres) and `PandasSkill` for high-throughput structured data analysis.
- **Provider Conformance Suite**: Implemented a mandatory symmetry test suite to ensure all future providers meet the "Institutional Grade" interface.
- **Environment Profiles**: `ModelFactory` now supports `env="production"` and `env="dev"` profiles for automatic model orchestration based on deployment context.

### Changed
- **Standardized Inference Interface**: Refactored the `InferenceProvider` ABC with a clean, polymorphic `run()` method and improved HF-style docstrings.
- **Dependency Isolation**: Gated local model and data analysis libraries behind optional extras (`[local]`, `[data]`) to keep the core engine lightweight.

## [0.1.2] - 2026-01-08

### Added
- **"Pure Core, Practical Shell" Architecture**: Re-engineered the platform to separate strict abstract logic from ergonomic high-level APIs.
- **Assistants Module**: Introduced `forecast.assistants` with high-level factories like `create_forecasting_analyst()` for one-line agent setup.
- **Flattened Namespace**: Key classes and factories (e.g., `ModelFactory`, `Orchestrator`, `TelemetryManager`) are now accessible directly at the module level (e.g., `from forecast.inference import ModelFactory`).
- **Smart Model Resolution**: `ModelFactory` and `Agent.from_config()` now support string shortcuts and model presets (e.g., `model="gemini"`).

### Changed
- **Decentralized Configuration**: Every major platform sub-package (`graph`, `telemetry`, `tools`) now owns its own `config.py`, removing dependencies on global singletons.
- **Branding Audit**: Removed all references to "CAFE" from the repository to ensure domain-agnosticism.

### Fixed
- **CI Mypy Stability**: Resolved a CI failure in GitHub Actions by exposing missing telemetry types in the ergonomic namespace.
- **Inference Injection**: Fixed a bug where API keys were not correctly injected from global settings into pure provider configs.

## [0.1.1] - 2026-01-07

### Added
- **Skill Protocol**: Introduced a new `forecast.skills` module for high-level, composable agent behaviors.
- **Evaluation Harness**: Added `forecast.eval` featuring a `Backtester` and `BrierScoreEvaluator` for institutional-grade accuracy benchmarking.
- **Structured Telemetry**: Global `TelemetryManager` and OTel-compatible `TelemetrySpan` hierarchy for deep observability.
- **Reference Implementation**: Explicitly labeled `ForecastingAnalyst` as a "Recipe" starter kit.

### Changed
- **Symmetrical Repository Layout**: Reorganized `examples/` and `tests/` into identical `core`, `features`, and `pipelines` hierarchies.
- **Generic Terminology**: Purged domain-specific terms like "market" and "capability" from core engine logic in favor of "subject" and "skill".
- **Documentation Overhaul**: Complete refactor of API documentation with new dedicated sections for platform components.

### Fixed
- **Telemetry Isolation**: Resolved a context manager bug in `TelemetrySpan` that prevented proper trace isolation in local environments.

## [0.1.0] - 2026-01-07

### Added
- **Unified "Everything is an Agent" Architecture**: Introduced `LLMAgent`, `ToolAgent`, and `GraphAgent` as core structural abstractions.
- **Institutional Specialist**: Created the `ForecastingAnalyst` persona in a new `specialists/` directory.
- **Double-Trace Telemetry**: Implemented both Structural (Audit Trail) and Logical (Reasoning Chain) tracing for execution results.
- **Universal Tool Calling**: Added a `ToolRegistry` with support for standard functions and `strand-agents` protocol adapters.
- **Robust Ingestion Layer**: New `LocalDataSource` and `PolymarketSource` for flexible data loading.
- **Production Infrastructure**: Integrated Redis-based distributed rate limiting and cryptographic signing for audit logs.
- **Professional Test Hierarchy**: Reorganized the test suite into `unit`, `integration`, and `e2e` tiers for better quality control.

### Changed
- **Directory Restructure**: Separated core abstractions from specialist implementations for better maintainability.
- **Professional Examples**: Renamed and upgraded examples to be high-fidelity, verified demonstrators.
- **Naming Alignment**: Renamed `MarketAnalyst` to `ForecastingAnalyst` to better reflect domain-agnosticism.

### Fixed
- **Orchestrator Cycle Limit**: Fixed a bug where `max_cycles` was not being correctly respected during graph execution.
- **Schema Validation**: Hardened the `LLMAgent` output parsing to handle malformed LLM responses and enforce Pydantic schemas.
