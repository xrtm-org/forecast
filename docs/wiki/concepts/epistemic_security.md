# Epistemic Security

## The Threat Model

In the age of AI-generated content, a forecasting engine faces a new threat:
**News Injection Attacks**.

A malicious actor can generate thousands of convincing fake articles about
"Company X Fraud" and inject them into an agent's context. An undefended
agent will believe this and make catastrophic decisions.

## Defense Layers

### 1. Source Verification (Passive Defense)
Every news item receives a `TrustScore` based on:
- Domain reputation and age
- Cross-reference with trusted outlets
- Historical accuracy of the source

```python
# Low-trust sources are suppressed
if news_item.trust_score < 0.3:
    context["warnings"].append("Unverified source")
```

### 2. Adversarial Testing (Active Defense)
The `AdversarialInjector` stress-tests agents by deliberately feeding them
fake news in a sandbox environment.

```python
from xrtm.forecast.kit.eval.resilience import AdversarialInjector

injector = AdversarialInjector()
fake = injector.generate_attack("ACME Corp", "bearish")

# Measure how much the agent's confidence shifts
report = injector.measure_resilience(
    initial_confidence=0.8,
    post_injection_confidence=agent_output.confidence
)

if report.resilience_score < 0.5:
    raise SecurityWarning("Agent is too gullible!")
```

## Metrics

| Metric | Good | Bad |
|--------|------|-----|
| `resilience_score` | > 0.7 | < 0.3 |
| `delta` (confidence shift) | < 0.2 | > 0.5 |

## Configuration

```python
# Paranoia levels
config = EpistemicConfig(
    paranoia_level="high",  # For trading
    # paranoia_level="low",  # For research
    min_trust_score=0.5,
    require_cross_reference=True
)
```
