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

import pytest

from examples.pipelines.custom_sentiment_workflow import run_custom_pipeline


@pytest.mark.asyncio
async def test_custom_graph_e2e(capsys):
    """
    Verifies that the custom graph example (Sentiment -> Trend) runs
    and produces the expected report output.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found. Skipping live custom graph integration test.")

    await run_custom_pipeline()

    captured = capsys.readouterr()
    assert "--- ADVANCED CUSTOM REPORT ---" in captured.out
    assert "Detected Sentiment:" in captured.out
    assert "Trend Multiplier:" in captured.out
    assert "Explanation:" in captured.out
