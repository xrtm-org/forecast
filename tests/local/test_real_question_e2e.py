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

import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from xrtm.forecast.e2e.real_questions import run_real_question_e2e


def _local_base_url() -> str:
    return os.getenv("XRTM_LOCAL_LLM_BASE_URL", "http://localhost:8080/v1").rstrip("/")


def _health_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        return base_url[:-3] + "/health"
    return base_url.rstrip("/") + "/health"


def _require_local_llm(base_url: str) -> None:
    request = Request(_health_url(base_url), method="GET")
    try:
        with urlopen(request, timeout=2) as response:
            if response.status != 200:
                pytest.fail(f"Local LLM endpoint returned HTTP {response.status}")
    except URLError as exc:
        pytest.fail(f"Local LLM endpoint is not reachable at {base_url}: {exc}")


@pytest.mark.local_llm
def test_real_question_e2e_local_llm_subset() -> None:
    r"""Run a bounded deterministic real-question corpus subset through local llama.cpp."""
    base_url = _local_base_url()
    _require_local_llm(base_url)

    records = run_real_question_e2e(
        limit=int(os.getenv("XRTM_FORECAST_REAL_E2E_LIMIT", "1")),
        base_url=base_url,
        model=os.getenv("XRTM_LOCAL_LLM_MODEL", "Qwen3.5-9B-UD-Q4_K_XL.gguf"),
        api_key=os.getenv("XRTM_LOCAL_LLM_API_KEY", "test"),
        max_tokens=int(os.getenv("XRTM_LOCAL_LLM_MAX_TOKENS", "768")),
        artifact_dir=Path("output/real-e2e-tests"),
    )

    assert records
    for record in records:
        assert record.question_id == record.output.question_id
        assert 0 <= record.output.probability <= 1
        assert record.output.reasoning.strip()
        assert record.output.metadata.created_at is not None
        assert record.output.metadata.snapshot_time is not None
        assert record.output.logical_trace
        assert record.output.structural_trace
