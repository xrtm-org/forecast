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
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    r"""
    Unified configuration settings for the xrtm-forecast platform.

    Settings are automatically loaded from environment variables with an optional
    `FORECAST_` prefix (e.g., `FORECAST_GEMINI_API_KEY`).
    """

    model_config = SettingsConfigDict(
        env_prefix="FORECAST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys are loaded from environment for convenience, but NOT used for global defaults.
    gemini_api_key: Optional[SecretStr] = Field(default=None, validation_alias="GEMINI_API_KEY")
    openai_api_key: Optional[SecretStr] = Field(default=None, validation_alias="OPENAI_API_KEY")
    tavily_api_key: Optional[SecretStr] = Field(default=None, validation_alias="TAVILY_API_KEY")

    # Global connection defaults
    default_rpm: int = 15
    default_timeout: int = 30


# Singleton instance for library-wide usage
# We initialize without arguments to allow Pydantic to load from environment variables automatically.
# The 'None' values in the previous version were confusing Mypy about the singleton's state.
settings = Settings()

__all__ = ["Settings", "settings"]
