# Epistemic Security

> **Removed in 0.9–0.10.** The `AdversarialInjector`, `GullibilityReport`, and
> `EpistemicEvaluator` tooling was removed from the engine. The current building
> blocks for robustness are:

- **Structured verification** — use `DecisionProvider` (e.g. `JevProvider`) with
  `EscalationRouter` to verify claims or route uncertain cases to a stronger model.
- **Source metadata** — `WebSearchSkill` returns structured `sources`,
  `results_count`, and timing, recorded in `metadata.raw_data["web_search"]`.
- **Parse integrity** — `ForecastOutput.parse_status` makes malformed model
  output explicit instead of silently degrading into a fallback forecast.
- **Temporal integrity** — `snapshot_time` and `MarketSnapshot` enforce
  zero-leakage boundaries.

See [Decisions](decisions.md) and [Inference](inference.md).
