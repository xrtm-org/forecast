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

from typing import Optional

from pydantic import BaseModel, Field, SecretStr


class ToolConfig(BaseModel):
    """Configuration for external tools and skill execution."""

    timeout: int = Field(default=30, description="Global timeout for tool execution in seconds.")
    tavily_api_key: Optional[SecretStr] = Field(default=None, description="API key for web search capabilities.")
    user_agent: str = Field(default="xrtm-forecast/0.1.2", description="User agent string for HTTP requests.")


__all__ = ["ToolConfig"]
