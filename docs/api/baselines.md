# Baselines

Zero-cost reference forecasts to compare LLM output against. The most
important one for prediction markets is the **market-implied probability**:
if your model cannot beat the market's own price, it is not adding value.

| Baseline | Returns |
|---|---|
| `MarketImpliedBaseline` | the market price from `question.context["market_price"]` (or `metadata.raw_data`), clamped to [0, 1] |
| `BaseRateBaseline` | the historical base rate of a set of binary outcomes |
| `ConstantBaseline` | a fixed probability (default 0.5) |

```python
from xrtm.forecast.kit.baselines import MarketImpliedBaseline

baseline = MarketImpliedBaseline()
probability = baseline.forecast(question)   # e.g. 0.42
```

`ConstantBaseline` is the sanity floor; `BaseRateBaseline` is the
"know nothing about this question" reference:

```python
from xrtm.forecast.kit.baselines import BaseRateBaseline

base_rate = BaseRateBaseline([1.0, 0.0, 1.0, 1.0])   # 0.75
```

## Using baselines in evaluation

Score the same resolved questions with xrtm-eval and compare Brier/ECE:

- market baseline vs LLM forecast → does the model add information?
- base-rate baseline vs LLM forecast → does the model beat the base rate?
- constant 0.5 → sanity floor (Brier 0.25 for balanced outcomes).

The ops evaluation loop records a free `baseline-market` entry for every
benchmark question, so this comparison happens automatically.
