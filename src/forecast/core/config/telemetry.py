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

from typing import List

from pydantic import BaseModel, Field


class TelemetryConfig(BaseModel):
    """Configuration for tracking, logging, and performance monitoring."""

    enable_masking: bool = Field(default=True, description="Whether to mask sensitive data (dates, names).")
    pii_patterns: List[str] = Field(default_factory=list, description="Extra regex patterns for custom masking.")
    verbosity: int = Field(default=1, description="Level of logging detail (0=silent, 2=debug).")
    export_otlp: bool = Field(default=False, description="Whether to export traces to an OTLP endpoint.")
    version: str = Field(default="0.1.2", description="The telemetry schema version.")


__all__ = ["TelemetryConfig"]
