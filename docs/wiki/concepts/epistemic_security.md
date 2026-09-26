# Epistemic Security

## The Threat Model

AI-generated content enables **news injection attacks**: a malicious actor can
flood an agent's context with convincing fake articles. An undefended agent
will believe them and make catastrophic decisions.

## Current Defense Layers (0.10)

> **Removed in 0.9–0.10.** The `AdversarialInjector`, `GullibilityReport`, and
> `EpistemicEvaluator` tooling was removed. Robustness now comes from engine
> primitives:

### 1. Structured verification

Use a `DecisionProvider` (e.g. `JevProvider`) with `EscalationRouter` to verify
claims or escalate uncertain ones to a stronger model:

```python
from xrtm.forecast.core.schemas.decision import DecisionOption
from xrtm.forecast.kit.decisions import EscalationRouter

router = EscalationRouter(primary=jev, fallback=llm, confidence_threshold=0.7)
verdict = await router.decide(
    "Claim: 'Company X committed fraud' — is it supported by the provided sources?",
    [DecisionOption(name="supported"), DecisionOption(name="unsupported")],
)
if verdict.decision != "supported" or verdict.confidence < 0.6:
    context["warnings"].append("Unverified claim")
```

### 2. Source metadata

`WebSearchSkill` returns structured `sources`, `results_count`, and
`search_time_ms`, stored under `metadata.raw_data["web_search"]` — so you can
audit which sources informed a forecast.

### 3. Parse integrity

`ForecastOutput.parse_status` marks malformed model output explicitly
(`invalid_json`, `empty_content`, `schema_error`) instead of silently degrading
into a fallback probability.

### 4. Temporal integrity

`snapshot_time` (metadata) and `MarketSnapshot` enforce zero-leakage
boundaries; search results must respect the snapshot window in backtests.

## Metrics

Track calibration and verification quality with `xrtm-eval` (Brier/ECE) and the
`confidence` distribution of your decision providers.
