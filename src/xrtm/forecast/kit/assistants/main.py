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

r"""
High-level factory functions for creating pre-configured agent specialists.

These 'Assistant' factories represent the 'Practical Shell' of the xrtm-forecast
platform, providing ergonomic shortcuts for common use cases while maintaining
the abstract integrity of the core engine.
r"""

import logging
from typing import Optional

from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.providers.inference.factory import ModelFactory

logger = logging.getLogger(__name__)


def create_forecasting_analyst(
    model_id: str = "openai:gpt-4o-mini", name: Optional[str] = None, **kwargs
) -> ForecastingAnalyst:
    r"""
    A high-level factory to create a pre-configured Forecasting Analyst.

    Args:
        model_id (`str`, *optional*, defaults to `"openai:gpt-4o-mini"`):
            The model identifier or shortcut string. Any OpenAI-compatible
            provider is supported (e.g., ``"openai:gpt-4o"`` or pass a config).
        name (`str`, *optional*):
            The logical name of the analyst.
        **kwargs:
            Additional arguments passed to the specialist constructor.

    Returns:
        `ForecastingAnalyst`: A fully wired specialist agent.
    r"""
    logger.debug(f"Creating pre-configured ForecastingAnalyst with model: {model_id}")
    model = ModelFactory.get_provider(model_id)
    return ForecastingAnalyst(model=model, name=name, **kwargs)


__all__ = ["create_forecasting_analyst"]

