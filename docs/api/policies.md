# Cost, Budget & Scheduling Policies

Currency-aware pricing, cost ledgers, hard budgets, and off-peak scheduling —
all engine-level, so applications do not re-implement provider pricing.

## Pricing

```python
from xrtm.forecast.core.policies import DEEPSEEK_CNY_PRICES, PriceTable, ModelPrice

# DeepSeek CNY rates (off-peak base; peak = 2x on weekdays)
cost = DEEPSEEK_CNY_PRICES.compute(
    "deepseek-flash",
    {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000},
)
assert DEEPSEEK_CNY_PRICES.currency == "CNY"
```

Bring your own table for other providers or currencies:

```python
table = PriceTable(
    currency="USD",
    prices={"my-model": ModelPrice(input_per_1m=0.5, output_per_1m=1.5, cached_input_per_1m=0.05)},
)
```

Peak windows are UTC hour ranges and are applied via `peak_multiplier`:

```python
from xrtm.forecast.core.policies import is_peak_time, seconds_until_off_peak
```

## Ledger & budget

```python
from xrtm.forecast.core.policies import BudgetPolicy, CostLedger

ledger = CostLedger(DEEPSEEK_CNY_PRICES, path="data/costs.jsonl")
budget = BudgetPolicy(ledger, daily_limit=1.0, total_limit=30.0)

ledger.record_output("deepseek-flash", forecast_output)   # prices output.usage
assert not budget.exceeded()
```

`BudgetPolicy.check()` raises `BudgetExceededError`; `remaining()` reports the
smallest remaining allowance across configured limits.

## Scheduling

```python
from xrtm.forecast.core.policies import SchedulePolicy

schedule = SchedulePolicy()
if schedule.is_peak():
    await asyncio.sleep(schedule.wait_seconds())
```

## Batch forecasting

```python
from xrtm.forecast.kit.batch import forecast_many

result = await forecast_many(agent, questions, concurrency=5, ledger=ledger, budget=budget)
print(len(result.outputs), result.skipped, result.cost, result.currency)
```

Remaining questions are skipped (and counted in `result.skipped`) once the
budget is exhausted.
