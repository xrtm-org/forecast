# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## [0.5.3] - 2026-01-25

### Fixed
- **Version Mismatch**: Synchronized project version to `0.5.3` across all metadata files to resolve PyPI upload conflicts.
- **Legacy Cleanup**: Removed stale build artifacts from `dist/` directory.

### Changed
- **Code Refinement**: Removed deprecated `AdversaryAgent` (redundant with `RedTeamAgent`).
- **Documentation**: Simplified "Key Features" heading in README.

## [0.5.2] - 2026-01-25

### Changed
- **Namespace Refactor**: Migrated package structure from `forecast` to `xrtm.forecast` Native Namespace Package.
- **Project Rename**: Renamed project to `xrtm-forecast` in `pyproject.toml`.

## [0.5.0] - 2026-01-22

### Added
- **Inference Cache**: SQLite-based LLM response caching with SHA256 hashing for 90% dev cost reduction (`core.cache.InferenceCache`).
- **Resilience Protocol**: Production-grade retry middleware with jittered exponential backoff and telemetry integration (`core.resilience.ResilientProvider`).
- **Wayback Integration**: Internet Archive tool for temporally-verified content retrieval with zero-leakage guarantee (`providers.tools.WaybackTool`).
- **30 New Tests**: Comprehensive test coverage for all v0.5.0 features.

### Changed
- **Master Plan**: Consolidated strategic roadmap in `.plans/master_plan.md`.
- **Idea Bank**: Expanded `.plans/ideas/` with 7 new strategic concepts (Cache, Resilience, Wayback, Decomposition, Tiered Intelligence, Benchmarks, Prompts).

## [0.4.3] - 2026-01-21

### Fixed
- **Privacy Hardening**: Implemented regex-based PII redaction (Email, Phone, API Keys, Credit Cards, SSN) in `Core.Anonymizer`.
- **Architecture Clarity**: Added a comprehensive Mermaid class dependency diagram to documentation.
- **Redundancy Cleanup**: Deprecated `AdversaryAgent` (Redundant with `RedTeamAgent`) to prepare for v0.5.0 cleanup.
- **Optimization Context**: Marked `BrierOptimizer` as experimental to align with its skeletal implementation.

## [0.4.2] - 2026-01-21

### Added
- **Institutional Coverage**: Achieved 91% core test coverage, resolving critical "Institutional Grade" debt.
- **Seamless Consensus**: `RecursiveConsensus` now natively supports Inverse Variance Weighting (IVW) and Red Team "Devil's Advocate" supervision.
- **Resilience Demo**: New `run_resilience_demo` showcasing `AdversarialInjector` and `GullibilityReport` for epistemic security testing.
- **Kit Exports**: Complete public API surface area for `forecast.kit`, exposing all agents and protocols.

### Fixed
- **Orchestration Cycles**: Resolved a logic mismatch where `Orchestrator` cycle limits could prematurely terminate revision loops.
- **Stranded Assets**: Fully integrated previously isolated modules (IVW, Red Team, Security) into the main topology.

## [0.4.1] - 2026-01-20

### Added
- **Schema Upgrade**: Added `uncertainty` field to `ForecastOutput` for Inverse Variance Weighting.
- **Inverse Variance Weighting**: Statistical aggregation method in `aggregation.py` for uncertainty-aware consensus.
- **Red Team Integration**: Wired `RedTeamAgent` into `RecursiveConsensus` topology via optional `red_team_wrapper`.
- **Adversarial Injector**: `AdversarialInjector` in `resilience.py` for epistemic stress-testing.
- **Documentation**: API docs for Sentinel Protocol and Epistemic Security modules.
- **Wiki Concepts**: Concept guides for Sentinel Protocol and Epistemic Security.

### Changed
- **mkdocs.yml**: Added navigation entries for new Sentinel and Security documentation.
- **Master Plan**: Added Phase 9 documenting v0.4.1 precision and integration work.


## [0.4.0] - 2026-01-20

### Added
- **Phase 5: Merkle Sovereignty**: Hash-chained state transitions in Orchestrator for tamper-evident audit trails.
- **Phase 5: Manifest Bundling**: `.xrtm` package format via `ManifestBundler` for portable research proofs.
- **Phase 5: Sovereignty Verifier**: Cryptographic validation of research proof bundles.
- **Phase 5: Epistemic Security**: Source verification with `TrustScore` and cross-reference checking.
- **Phase 6: Causal DAGs**: `CausalNode` and `CausalEdge` schemas with `networkx` integration.
- **Phase 6: Intervention Engine**: Do-calculus API for "What-If" analysis.
- **Phase 7: Beta Calibration**: `BetaScaler` for asymmetric non-parametric error distributions.
- **Phase 7: Prompt Optimization**: DSPy-style `BrierOptimizer` and `CompiledAgent` for automated prompt tuning.
- **Phase 8: Centaur Protocol**: `HumanProvider` interface and `AnalystWorkbench` for human-AI collaborative forecasting.
- **Phase 8: Bias Interceptor**: Cognitive bias auditor for human forecasters.
- **Sentinel Protocol**: `PollingDriver` for dynamic forecasting with trajectory updates.
- **Red Team Agent**: Devil's Advocate pattern for adversarial consensus hardening.
- **Wiki Docs**: Concept guides for Temporal Integrity, Merkle Sovereignty, and Human-in-the-Loop.

### Changed
- **CONTRIBUTING.md**: Enhanced with three-layer architecture overview and key coding standards.
- **Domain Agnosticism**: Standardized terminology to "Subject/Value" instead of "Market/Price".
- **AsyncRuntime**: Added mandatory `parent_id` for task lineage tracking.


## [0.3.2] - 2026-01-14

### Changed
- **Deep Institutional Hardening**: Reached 90%+ core coverage for `Orchestrator` (91%) and `AsyncRuntime` (97%).
- **Terminology Standardization**: Unified graph execution terminology around "Stages" (Rule 17).
- **Docstring Rigor**: Enforced strict Rule 2 (Hugging Face style) compliance across all public core interfaces.

### Added
- **Runtime Patterns Example**: Created `examples/core/runtime_patterns/` to demonstrate institutional structured concurrency.

## [0.3.1] - 2026-01-13

### Changed
- **Async Runtime Standardization**: Promoted `AsyncRuntime` to a top-level export and updated all user-facing documentation/examples to use the managed runtime instead of raw `asyncio`.
- **Strategic Roadmap Synchronization**: Fully reconciled the Master Implementation Plan and public Roadmap with the latest "Institutional Grade" strategic research logs.

### Added
- **"Show & Prove" Assets**: Created self-contained demonstration scripts for the `FactChecker` and `Adversary` agents to ensure 100% feature-parity in documentation.
- **TaskGroup Support**: Enhanced the `AsyncRuntime` with native `TaskGroup` support for structured concurrency in Python 3.11+.


### Added
- **Chronos Protocol (Backtest Integrity)**: Introduced `TemporalContext` and `GuardianTool` to enforce strict point-in-time safety during time-travel simulations and backtests.
- **Sentinel Protocol (Trajectory Forecasting)**: Standardized `ForecastTrajectory` and `TimeSeriesPoint` schemas for tracking the evolution of probability distributions over time.
- **Recursive Consensus Topology**: Implemented the `RecursiveConsensus` pattern for iterative agent refinement with supervisor feedback loops.
- **Fact-Checker Agent**: New specialist agent for automated claim extraction and multi-tool verification.
- **Async Runtime Facade**: Added `AsyncRuntime` as a safety layer for managing background tasks and preventing asyncio common pitfalls.

### Changed
- **Institutional Alignment (The Big Shuffle)**: Reorganized `/core` and `/kit` to strictly separate platform physics from application templates.
- **Conditional Routing**: Enhanced the `Orchestrator` with first-class `conditional_edge` support for state-dependent logic.
- **Documentation Standards**: Enforced mandatory Apache 2.0 license headers and structured docstrings across 100% of the codebase via automated auditing.

### Fixed
- **Rate-Limiting Stability**: Hardened the Redis-based rate limiter to support `AsyncRuntime` sleeping.
- **E2E Path Integrity**: Resolved relative path regressions in pipeline data ingestion after the architectural move.

## [0.2.1] - 2026-01-09

### Added
- **Scenario Branching**: Introduced `ScenarioManager` and `state_ops.clone_state` for parallel "What-If" analysis.
- **Deterministic Trace Replay**: Added `TraceReplayer` and decoupled `BacktestRunner.evaluate_state` for offline re-scoring.
- **Metadata Slicing**: Implemented `SliceAnalytics` and `EvaluationReport.slices` for automated sub-group performance analysis.
- **Deep Copy Utility**: `clone_state` now supports Pydantic models with explicit overrides for safe branching.

### Changed
- **Directory Structure**: strict mirroring of `/core`, `/kit`, and `/providers` in `examples/` directory.
- **Evaluation Report**: Schema updated to include recursive `slices` for sub-reports.

## [0.2.0] - 2026-01-09

### Changed
- **Major Architecture Refactor**: Migrated to "Pure Core / The Kit" architecture.
    - `/core`: Zero-dependency protocols and orchestrator.
    - `/kit`: Importable agents, skills, and evaluators.
    - `/providers`: Concrete inference and tool implementations.
- **Module Relocation**:
    - `src/forecast/agents/` -> `src/forecast/kit/agents/`
    - `src/forecast/skills/` -> `src/forecast/kit/skills/`
    - `src/forecast/inference/` -> `src/forecast/providers/inference/`

## [0.1.5] - 2026-01-08

### Added
- **Composable Topologies**: Introduced factory functions for advanced architectural patterns, including `DebateTopology` and `FanOutTopology`.
- **Parallel Group Execution**: Enhanced the `Orchestrator` to support concurrent node execution with barrier synchronization for high-throughput workflows.
- **Streaming Sovereignty**: Standardized asynchronous streaming across all providers (OpenAI, Gemini, and Local Hugging Face).
- **Visualization & Bias Tools**: Added `ReliabilityDiagram` in `forecast.eval.viz` to detect and visualize model overconfidence and calibration bias.
- **Deep Dive Wiki**: Restructured documentation into a hierarchical concept-based Wiki for improved developer onboarding.

### Fixed
- **State Race Conditions**: Resolved a non-deterministic state mutation bug in parallel execution groups.
- **Numerical Stability**: Fixed division-by-zero edge cases in calibration calculations.
- **Orchestration Resilience**: Added explicit error propagation and logging for failed parallel nodes.

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
- **Flattened Namespace**: Key classes and factories (e.g., `ModelFactory`, `Orchestrator`, `TelemetryManager`) are now accessible directly at the module level (e.g., `from xrtm.forecast.inference import ModelFactory`).
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
