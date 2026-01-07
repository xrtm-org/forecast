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
import time
from collections import deque
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TokenStreamContext:
    """
    Singleton circular buffer to store the last N LLM interactions.
    Used for live debugging, compliance verification, and visualization.
    """

    _instance = None
    _buffer: deque

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenStreamContext, cls).__new__(cls)
            cls._instance._buffer = deque(maxlen=100)  # Keep last 100 requests
        return cls._instance

    def log(
        self,
        prompt: str,
        response: str,
        model_id: str,
        token_usage: Dict[str, int],
        latency_ms: float,
        component_id: str = "unknown",
    ):
        """Push a new interaction record into the stream."""
        record = {
            "timestamp": time.time(),
            "id": f"{int(time.time() * 1000)}",
            "component": component_id,
            "model": model_id,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "prompt_full": prompt,
            "response_preview": response[:100] + "..." if len(response) > 100 else response,
            "response_full": response,
            "usage": token_usage,
            "latency_ms": latency_ms,
        }
        self._buffer.append(record)

    def get_history(self) -> List[Dict[str, Any]]:
        """Return the current buffer as a list."""
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()
