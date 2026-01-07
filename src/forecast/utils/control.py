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

logger = logging.getLogger(__name__)


class ControlService:
    """
    Manages the global execution state (PAUSE/RESUME/HALT) of an agent swarm.
    Uses Redis as the source of truth to allow external control (CLI/Dashboard).
    """

    KEY_SYSTEM_STATUS = "FORECAST_CONTROL_STATUS"
    STATUS_RUNNING = "RUNNING"
    STATUS_PAUSED = "PAUSED"
    STATUS_HALTED = "HALTED"

    def __init__(self, redis_url: str, key_prefix: str = "FORECAST"):
        self.key = f"{key_prefix}_CONTROL_STATUS"
        try:
            import redis

            self.redis = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.error(f"[CONTROL] Failed to connect to Redis: {e}")
            self.redis = None

    def is_paused(self) -> bool:
        """Returns True if the system is globally paused."""
        if not self.redis:
            return False
        try:
            return self.redis.get(self.key) == self.STATUS_PAUSED
        except Exception:
            return False

    def is_halted(self) -> bool:
        """Returns True if the system is globally halted (critical stop)."""
        if not self.redis:
            return False
        try:
            return self.redis.get(self.key) == self.STATUS_HALTED
        except Exception:
            return False

    def pause(self):
        """Set state to PAUSED."""
        if self.redis:
            self.redis.set(self.key, self.STATUS_PAUSED)
            logger.warning(f"[CONTROL] Swarm set to PAUSED ({self.key})")

    def resume(self):
        """Set state to RUNNING."""
        if self.redis:
            self.redis.set(self.key, self.STATUS_RUNNING)
            logger.info(f"[CONTROL] Swarm set to RUNNING ({self.key})")

    def halt(self):
        """Set state to HALTED."""
        if self.redis:
            self.redis.set(self.key, self.STATUS_HALTED)
            logger.error(f"[CONTROL] Swarm set to HALTED ({self.key})")

    def get_status(self) -> str:
        if not self.redis:
            return "UNKNOWN"
        return self.redis.get(self.key) or self.STATUS_RUNNING
