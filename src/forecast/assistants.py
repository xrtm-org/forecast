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
"""

import logging
from typing import Optional

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.inference.factory import ModelFactory

logger = logging.getLogger(__name__)


def create_forecasting_analyst(
    model_id: str = "gemini:gemini-2.0-flash",
    name: Optional[str] = None,
    **kwargs
) -> ForecastingAnalyst:
    r"""
    A high-level factory to create a pre-configured Forecasting Analyst.

    Args:
        model_id (`str`, *optional*, defaults to `"gemini:gemini-2.0-flash"`):
            The model identifier or shortcut string.
        name (`str`, *optional*):
            The logical name of the analyst.
        **kwargs:
            Additional arguments passed to the specialist constructor.

    Returns:
        `ForecastingAnalyst`: A fully wired specialist agent.
    """
    logger.debug(f"Creating pre-configured ForecastingAnalyst with model: {model_id}")

    # Resolver logic: ModelFactory handles strings or Config objects
    model = ModelFactory.get_provider(model_id)

    # Specialist instantiation
    return ForecastingAnalyst(model=model, name=name, **kwargs)


def create_local_analyst(
    model_path: str = "sshleifer/tiny-gpt2",
    name: Optional[str] = None,
    **kwargs
) -> ForecastingAnalyst:
    r"""
    Creates a Forecasting Analyst backed by a local Hugging Face model.

    This is the primary entry point for 'Air-gapped' or 'Sovereign' reasoning
    pipelines where data privacy is requirements.

    Args:
        model_path (`str`, *optional*, defaults to `"sshleifer/tiny-gpt2"`):
            The local path or Hugging Face repo ID.
        name (`str`, *optional*):
            The logical name of the analyst.
        **kwargs:
            Additional arguments passed to the specialist (e.g., quantization="4bit").

    Returns:
        `ForecastingAnalyst`: A private specialist agent.
    """
    logger.info(f"Creating local ForecastingAnalyst from: {model_path}")

    # Use 'hf:' prefix to force local resolution in ModelFactory
    model = ModelFactory.get_provider(f"hf:{model_path}", **kwargs)

    return ForecastingAnalyst(model=model, name=name, **kwargs)


__all__ = ["create_forecasting_analyst", "create_local_analyst"]
