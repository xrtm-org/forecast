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

from pydantic import BaseModel, Field


class GraphConfig(BaseModel):
    """Configuration for the Orchestrator reasoning engine."""

    max_cycles: int = Field(default=3, description="Maximum number of state-machine iterations.")
    entry_node: str = Field(default="ingestion", description="Initial node to start execution from.")
    timeout: Optional[float] = Field(default=None, description="Global timeout for the entire graph run.")

__all__ = ["GraphConfig"]
