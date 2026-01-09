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

import logging
import os

from pydantic import SecretStr

from forecast.core.config.inference import GeminiConfig, OpenAIConfig


def get_example_config(provider: str = "gemini"):
    """
    Returns a standardized config for examples based on environment variables.
    Provides a central place to swap models for all example scripts.
    """
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "mock-key")
        return GeminiConfig(api_key=SecretStr(api_key), model_id=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"))
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "mock-key")
        return OpenAIConfig(api_key=SecretStr(api_key), model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def setup_example_logging():
    """Sets up a clean logging format for examples."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
