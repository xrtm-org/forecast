# Epistemic Security API

The security module provides tools for **Adversarial Resilience** — stress-testing
agents against fake news and manipulation attacks.

## Core Classes

### `AdversarialInjector`
A Red Team tool that generates fake news to test agent gullibility.

```python
from forecast.kit.eval.resilience import AdversarialInjector

injector = AdversarialInjector(intensity=0.5)
fake = injector.generate_attack("Tesla", direction="bearish")
# FakeNewsItem(headline="BREAKING: Tesla CEO Under Investigation...")
```

### `FakeNewsItem`
Schema for synthetic attack content.

| Field | Type | Description |
|-------|------|-------------|
| `headline` | `str` | The fake headline |
| `source_domain` | `str` | Fake source (default: low-trust) |
| `content` | `str` | Article body |
| `trust_score` | `float` | Default 0.1 (very low) |
| `intended_bias` | `str` | "Bearish" or "Bullish" |

### `GullibilityReport`
The result of a resilience test.

```python
report = injector.measure_resilience(
    initial_confidence=0.8,
    post_injection_confidence=0.3
)
# GullibilityReport(delta=-0.5, resilience_score=0.5)
```

| Field | Type | Description |
|-------|------|-------------|
| `initial_confidence` | `float` | Before fake news |
| `post_injection_confidence` | `float` | After fake news |
| `delta` | `float` | Change in confidence |
| `resilience_score` | `float` | 0.0 (collapsed) to 1.0 (immune) |
