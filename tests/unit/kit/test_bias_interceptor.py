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

from forecast.kit.eval.bias import BiasInterceptor


@pytest.mark.asyncio
async def test_bias_interceptor_detection():
    r"""Verifies that the BiasInterceptor correctly prompts the model for audit."""

    # 1. Setup Mock Model
    mock_model = AsyncMock()
    mock_model.generate.return_value.text = '{"detected_biases": ["Overconfidence"], "severity": 8}'

    # 2. Setup Interceptor
    interceptor = BiasInterceptor(model=mock_model)

    # 3. Execute
    reasoning = "I am 100% certain that AI will solve all problems because I just read a cool blog post."
    audit = await interceptor.evaluate_reasoning(reasoning)

    # 4. Assertions
    assert mock_model.generate.called
    call_args = mock_model.generate.call_args[0][0]
    assert "Cognitive Bias Auditor" in call_args
    assert reasoning in call_args
    assert audit["raw_audit"] == '{"detected_biases": ["Overconfidence"], "severity": 8}'
