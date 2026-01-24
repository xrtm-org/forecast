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

from unittest.mock import AsyncMock

import pytest

from xrtm.forecast.kit.agents.prompting import CompiledAgent, PromptTemplate
from xrtm.forecast.kit.optimization.compiler import BrierOptimizer


@pytest.mark.asyncio
async def test_brier_optimizer_loop():
    r"""Verifies that the optimizer correctly generates a new prompt based on feedback."""

    # 1. Setup Mock Optimizer Model
    mock_model = AsyncMock()
    mock_model.generate.return_value = "Optimized: Be more conservative."

    # 2. Setup Agent
    template = PromptTemplate(instruction="Forecast everything.")
    agent_model = AsyncMock()
    agent = CompiledAgent(model=agent_model, template=template)

    # 3. Setup Optimizer
    optimizer = BrierOptimizer(optimizer_model=mock_model)

    # 4. Simulation Data (Input, Pred, Truth)
    dataset = [
        ("Will AI win?", 0.9, 0),  # Error: Overconfident
        ("Will humans win?", 0.1, 1),  # Error: Underconfident
    ]

    # 5. Execute Optimization
    new_template = await optimizer.optimize(agent, dataset)

    assert new_template.version == 2
    assert new_template.instruction == "Optimized: Be more conservative."
    assert mock_model.generate.called

    # Verify the prompt sent to the optimizer contains the score
    call_args = mock_model.generate.call_args[0][0]
    assert "Current Goal: Minimize Brier Score" in call_args
    assert "0.8100" in call_args  # ((0.9-0)^2 + (0.1-1)^2) / 2 = (0.81 + 0.81) / 2 = 0.81
