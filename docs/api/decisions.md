# Decisions

Typed decision providers answer **bounded choice problems**: given a state and a
list of options, they return a choice, a confidence, and (when available) a
probability per option.

Two families implement the same `DecisionProvider` contract:

| Provider | Backend | Typical use |
|---|---|---|
| `LLMDecisionProvider` | Any `InferenceProvider` (JSON-mode LLM) | Routing, gating, verification with models you already run |
| `JevProvider` | TypeSafe Jev via an OpenAI-compatible gateway | Fast, cheap System-One decisions |

## Quick start

```python
from xrtm.forecast.core.schemas.decision import DecisionOption
from xrtm.forecast.providers.inference.decision import LLMDecisionProvider
from xrtm.forecast.providers.inference.factory import ModelFactory

model = ModelFactory.get_provider("openai:deepseek-flash")  # or any InferenceProvider
decider = LLMDecisionProvider(model=model)

result = await decider.decide(
    "Polymarket market: 'Will X happen?' at 0.42 with 3% spread.",
    [
        DecisionOption(name="trade", description="Open a position"),
        DecisionOption(name="skip", description="No edge"),
    ],
)
print(result.decision, result.confidence, result.probabilities)
```

## Escalation routing

`EscalationRouter` keeps the cheap provider in front and escalates uncertain
decisions to a stronger fallback:

```python
from xrtm.forecast.kit.decisions import EscalationRouter

router = EscalationRouter(
    primary=jev_provider,
    fallback=llm_decider,
    confidence_threshold=0.7,
)
result = await router.decide(state, options)
assert result.escalated in (True, False)
```

## Jev configuration

`JevProvider` reads `JEV_BASE_URL` and `JEV_API_KEY` (or takes them
explicitly) and targets an OpenAI-compatible gateway that serves Jev. Its
`answers` envelope is unwrapped into the shared `DecisionResult` shape; use
`answer_key=` when a request returns multiple named answers.
