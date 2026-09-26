# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""Cost, budget, and scheduling policies.

Currency-aware pricing with peak/off-peak windows, an optional JSONL cost
ledger, hard budget limits, and schedule helpers for deferring work into
cheaper windows.

Ships a DeepSeek CNY preset (matching the official rates for accounts topped
up in CNY), but any :class:`PriceTable` can be supplied.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from pydantic import BaseModel, Field

from xrtm.forecast.core.exceptions import BudgetExceededError

logger = logging.getLogger(__name__)

__all__ = [
    "ModelPrice",
    "PriceTable",
    "CostLedger",
    "BudgetPolicy",
    "SchedulePolicy",
    "DEEPSEEK_CNY_PRICES",
    "PEAK_WINDOWS_UTC",
    "is_peak_time",
    "seconds_until_off_peak",
]

# Peak windows as UTC hour ranges [start, end) — DeepSeek peak = Beijing
# Mon-Fri 09:00-12:00 and 14:00-18:00.
PEAK_WINDOWS_UTC: Tuple[Tuple[int, int], ...] = ((1, 4), (6, 10))


def is_peak_time(at: Optional[datetime] = None, windows: Tuple[Tuple[int, int], ...] = PEAK_WINDOWS_UTC) -> bool:
    r"""True when *at* falls in a weekday peak-pricing window (UTC)."""
    moment = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if moment.weekday() >= 5:  # Saturday/Sunday are always off-peak
        return False
    return any(start <= moment.hour < end for start, end in windows)


def seconds_until_off_peak(
    at: Optional[datetime] = None,
    windows: Tuple[Tuple[int, int], ...] = PEAK_WINDOWS_UTC,
) -> float:
    r"""Seconds until the next off-peak window (0.0 when already off-peak)."""
    moment = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not is_peak_time(moment, windows):
        return 0.0
    for start, end in windows:
        if start <= moment.hour < end:
            end_time = moment.replace(hour=end, minute=0, second=0, microsecond=0)
            return max(0.0, (end_time - moment).total_seconds())
    return 0.0


def _usage_value(usage: Union[Dict[str, int], Any], key: str) -> int:
    if isinstance(usage, dict):
        return int(usage.get(key, 0) or 0)
    return int(getattr(usage, key, 0) or 0)


class ModelPrice(BaseModel):
    r"""Per-1M-token prices for one model.

    Attributes:
        input_per_1m: Price per 1M cache-miss input tokens.
        output_per_1m: Price per 1M output tokens.
        cached_input_per_1m: Price per 1M cache-hit input tokens.
    """

    input_per_1m: float = Field(..., ge=0, description="Price per 1M cache-miss input tokens")
    output_per_1m: float = Field(..., ge=0, description="Price per 1M output tokens")
    cached_input_per_1m: float = Field(default=0.0, ge=0, description="Price per 1M cache-hit input tokens")


class PriceTable(BaseModel):
    r"""A currency-aware price table with optional peak pricing.

    Attributes:
        currency: Currency code for every price in the table (e.g. ``"CNY"``).
        prices: Model id to :class:`ModelPrice` mapping.
        default_price: Fallback price for unknown models.
        peak_multiplier: Multiplier applied during peak windows (1.0 = none).
        peak_windows: UTC hour ranges ``[start, end)`` treated as peak.
    """

    currency: str = Field(default="USD", description="Currency code for every price in this table")
    prices: Dict[str, ModelPrice] = Field(default_factory=dict, description="Model id to price mapping")
    default_price: Optional[ModelPrice] = Field(default=None, description="Fallback price for unknown models")
    peak_multiplier: float = Field(default=1.0, ge=1.0, description="Multiplier applied during peak windows")
    peak_windows: Tuple[Tuple[int, int], ...] = Field(
        default=(),
        description="UTC hour ranges [start, end) treated as peak",
    )

    def price_for(self, model_id: str) -> ModelPrice:
        r"""Return the :class:`ModelPrice` for *model_id*, falling back to the default."""
        if model_id in self.prices:
            return self.prices[model_id]
        if self.default_price is not None:
            return self.default_price
        raise KeyError(f"No price registered for model {model_id!r}")

    def multiplier(self, at: Optional[datetime] = None) -> float:
        r"""Return the peak multiplier active at *at* (1.0 when off-peak)."""
        if self.peak_multiplier <= 1.0 or not self.peak_windows:
            return 1.0
        return self.peak_multiplier if is_peak_time(at, self.peak_windows) else 1.0

    def compute(self, model_id: str, usage: Union[Dict[str, int], Any], at: Optional[datetime] = None) -> float:
        r"""Compute the cost of *usage* for *model_id* in this table's currency."""
        price = self.price_for(model_id)
        prompt = _usage_value(usage, "prompt_tokens")
        completion = _usage_value(usage, "completion_tokens")
        cached = _usage_value(usage, "cached_prompt_tokens")
        uncached = max(0, prompt - cached)

        cost = (
            (uncached / 1_000_000) * price.input_per_1m
            + (cached / 1_000_000) * price.cached_input_per_1m
            + (completion / 1_000_000) * price.output_per_1m
        )
        return cost * self.multiplier(at)


_FLASH_CNY = ModelPrice(input_per_1m=1.0, cached_input_per_1m=0.02, output_per_1m=4.0)
_PRO_CNY = ModelPrice(input_per_1m=4.5, cached_input_per_1m=0.15, output_per_1m=13.5)

#: DeepSeek CNY price table (off-peak base rates; peak = 2x on weekdays).
DEEPSEEK_CNY_PRICES = PriceTable(
    currency="CNY",
    prices={
        "deepseek-flash": _FLASH_CNY,
        "deepseek-chat": _FLASH_CNY,
        "deepseek-v4-flash": _FLASH_CNY,
        "deepseek-v4-pro": _PRO_CNY,
    },
    default_price=_FLASH_CNY,
    peak_multiplier=2.0,
    peak_windows=PEAK_WINDOWS_UTC,
)


class CostLedger:
    r"""Cost accounting with optional JSONL persistence.

    Args:
        price_table: The :class:`PriceTable` used to price recorded usage.
        path: Optional JSONL file to append records to and load from.
    """

    def __init__(self, price_table: PriceTable, path: Optional[Union[str, Path]] = None):
        self.price_table = price_table
        self.path = Path(path) if path is not None else None
        self._records: list[Dict[str, Any]] = []
        if self.path is not None and self.path.exists():
            self._load()

    def record_usage(
        self,
        model_id: str,
        usage: Union[Dict[str, int], Any],
        at: Optional[datetime] = None,
    ) -> float:
        r"""Price *usage*, append a record, and return the cost."""
        moment = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        cost = self.price_table.compute(model_id, usage, moment)
        record = {
            "timestamp": moment.isoformat(),
            "model": model_id,
            "currency": self.price_table.currency,
            "cost": cost,
            "prompt_tokens": _usage_value(usage, "prompt_tokens"),
            "completion_tokens": _usage_value(usage, "completion_tokens"),
            "cached_prompt_tokens": _usage_value(usage, "cached_prompt_tokens"),
            "peak": self.price_table.multiplier(moment) > 1.0,
        }
        self._records.append(record)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a") as handle:
                handle.write(json.dumps(record) + "\n")
        return cost

    def record_output(self, model_id: str, output: Any, at: Optional[datetime] = None) -> float:
        r"""Price an object carrying a ``usage`` attribute (e.g. ``ForecastOutput``)."""
        return self.record_usage(model_id, getattr(output, "usage", None) or {}, at=at)

    @property
    def total(self) -> float:
        r"""Total recorded cost in the table's currency."""
        return sum(float(record.get("cost", 0.0)) for record in self._records)

    def daily_total(self, day: Optional[str] = None) -> float:
        r"""Total recorded cost for one UTC day (default: today)."""
        target = day or datetime.now(timezone.utc).date().isoformat()
        return sum(float(record.get("cost", 0.0)) for record in self._records if record.get("timestamp", "")[:10] == target)

    @property
    def records(self) -> list[Dict[str, Any]]:
        r"""All recorded cost entries."""
        return list(self._records)

    def _load(self) -> None:
        assert self.path is not None
        try:
            with open(self.path) as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._records.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed cost ledger line in %s", self.path)
        except OSError:
            logger.warning("Could not load cost ledger from %s", self.path)


class BudgetPolicy:
    r"""Hard budget limits over a :class:`CostLedger`.

    Args:
        ledger: Ledger to check.
        daily_limit: Maximum spend per UTC day (None = unlimited).
        total_limit: Maximum total spend (None = unlimited).
    """

    def __init__(
        self,
        ledger: CostLedger,
        daily_limit: Optional[float] = None,
        total_limit: Optional[float] = None,
    ):
        self.ledger = ledger
        self.daily_limit = daily_limit
        self.total_limit = total_limit

    def exceeded(self) -> bool:
        r"""True when any configured limit has been reached."""
        if self.daily_limit is not None and self.ledger.daily_total() >= self.daily_limit:
            return True
        if self.total_limit is not None and self.ledger.total >= self.total_limit:
            return True
        return False

    def remaining(self) -> Optional[float]:
        r"""Smallest remaining budget across configured limits (None = unlimited)."""
        remaining: list[float] = []
        if self.daily_limit is not None:
            remaining.append(self.daily_limit - self.ledger.daily_total())
        if self.total_limit is not None:
            remaining.append(self.total_limit - self.ledger.total)
        return max(0.0, min(remaining)) if remaining else None

    def check(self) -> None:
        r"""Raise :class:`BudgetExceededError` when a limit has been reached."""
        if self.exceeded():
            raise BudgetExceededError(
                f"Budget exceeded ({self.ledger.price_table.currency}): "
                f"daily_spend={self.ledger.daily_total():.6f}, total_spend={self.ledger.total:.6f}"
            )


class SchedulePolicy:
    r"""Decide when work should run to stay in cheaper (off-peak) windows.

    Args:
        windows: UTC hour ranges ``[start, end)`` treated as peak.
        enabled: When False, everything counts as off-peak.
    """

    def __init__(self, windows: Tuple[Tuple[int, int], ...] = PEAK_WINDOWS_UTC, enabled: bool = True):
        self.windows = tuple(windows)
        self.enabled = enabled

    def is_peak(self, at: Optional[datetime] = None) -> bool:
        r"""True when *at* is inside a peak window and scheduling is enabled."""
        return self.enabled and is_peak_time(at, self.windows)

    def wait_seconds(self, at: Optional[datetime] = None) -> float:
        r"""Seconds to wait until the next off-peak window (0 when already off-peak)."""
        return seconds_until_off_peak(at, self.windows) if self.enabled else 0.0
