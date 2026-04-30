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

r"""Unit tests for forecast.core.telemetry.token_stream."""

from xrtm.forecast.core.telemetry import token_stream
from xrtm.forecast.core.telemetry.token_stream import TokenStreamContext


def test_token_stream_context_records_deterministic_time(monkeypatch):
    r"""Should make time-derived fields deterministic when time is frozen."""
    monkeypatch.setattr(token_stream.time, "time", lambda: 1234.567)
    context = TokenStreamContext()
    context.clear()

    context.log(
        prompt="p" * 101,
        response="r" * 101,
        model_id="model",
        token_usage={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        latency_ms=4.5,
        component_id="component",
    )

    assert context.get_history() == [
        {
            "timestamp": 1234.567,
            "id": "1234567",
            "component": "component",
            "model": "model",
            "prompt_preview": ("p" * 100) + "...",
            "prompt_full": "p" * 101,
            "response_preview": ("r" * 100) + "...",
            "response_full": "r" * 101,
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            "latency_ms": 4.5,
        }
    ]


def test_token_stream_context_rolls_over_at_capacity(monkeypatch):
    r"""Should retain only the last 100 interaction records."""
    current_time = 0.0

    def fake_time() -> float:
        nonlocal current_time
        current_time += 1.0
        return current_time

    monkeypatch.setattr(token_stream.time, "time", fake_time)
    context = TokenStreamContext()
    context.clear()

    for i in range(101):
        context.log(
            prompt=f"prompt-{i}",
            response=f"response-{i}",
            model_id="model",
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            latency_ms=0.0,
        )

    history = context.get_history()
    assert len(history) == 100
    assert history[0]["prompt_full"] == "prompt-1"
    assert history[-1]["prompt_full"] == "prompt-100"
