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

from examples.features.external_strand_tools import main as run_external_tools_example


@pytest.mark.asyncio
async def test_external_tools_e2e(capsys):
    """
    Verifies the external tool integration example handshake.
    Note: Requires GEMINI_API_KEY for a real LLM run,
    otherwise skips with a message.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found. Skipping live LLM integration test.")

    await run_external_tools_example()

    captured = capsys.readouterr()
    assert "FINAL AGENT REPORT (Using External Strand Tool):" in captured.out
    assert "[App] Ingesting external tool: get_market_sentiment" in captured.out
