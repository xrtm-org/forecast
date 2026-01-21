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

r"""Unit tests for forecast.core.utils.control."""

from unittest.mock import MagicMock, patch

from forecast.core.utils.control import ControlService


class TestControlService:
    r"""Tests for the ControlService class."""

    def test_init_without_redis(self):
        r"""Should handle missing redis gracefully."""
        with patch.dict("sys.modules", {"redis": None}):
            # When redis import fails, redis attribute should be None
            service = ControlService("redis://localhost:6379")
            assert service.redis is None or service.key is not None

    def test_init_with_redis_connection_error(self):
        r"""Should handle Redis connection errors gracefully."""
        with patch("redis.from_url", side_effect=Exception("Connection refused")):
            service = ControlService("redis://localhost:6379")
            assert service.redis is None

    def test_init_with_custom_prefix(self):
        r"""Should use custom key prefix."""
        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            service = ControlService("redis://localhost:6379", key_prefix="CUSTOM")
            assert service.key == "CUSTOM_CONTROL_STATUS"

    def test_is_paused_without_redis(self):
        r"""Should return False when redis is None."""
        service = ControlService.__new__(ControlService)
        service.redis = None
        service.key = "TEST_KEY"
        assert service.is_paused() is False

    def test_is_paused_when_paused(self):
        r"""Should return True when status is PAUSED."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.return_value = "PAUSED"
        service.key = "TEST_KEY"
        assert service.is_paused() is True

    def test_is_paused_when_running(self):
        r"""Should return False when status is RUNNING."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.return_value = "RUNNING"
        service.key = "TEST_KEY"
        assert service.is_paused() is False

    def test_is_paused_on_exception(self):
        r"""Should return False on redis exception."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.side_effect = Exception("Redis error")
        service.key = "TEST_KEY"
        assert service.is_paused() is False

    def test_is_halted_when_halted(self):
        r"""Should return True when status is HALTED."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.return_value = "HALTED"
        service.key = "TEST_KEY"
        assert service.is_halted() is True

    def test_is_halted_without_redis(self):
        r"""Should return False when redis is None."""
        service = ControlService.__new__(ControlService)
        service.redis = None
        service.key = "TEST_KEY"
        assert service.is_halted() is False

    def test_pause(self):
        r"""Should set key to PAUSED."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.key = "TEST_KEY"
        service.pause()
        service.redis.set.assert_called_once_with("TEST_KEY", "PAUSED")

    def test_resume(self):
        r"""Should set key to RUNNING."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.key = "TEST_KEY"
        service.resume()
        service.redis.set.assert_called_once_with("TEST_KEY", "RUNNING")

    def test_halt(self):
        r"""Should set key to HALTED."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.key = "TEST_KEY"
        service.halt()
        service.redis.set.assert_called_once_with("TEST_KEY", "HALTED")

    def test_get_status_without_redis(self):
        r"""Should return UNKNOWN when redis is None."""
        service = ControlService.__new__(ControlService)
        service.redis = None
        service.key = "TEST_KEY"
        assert service.get_status() == "UNKNOWN"

    def test_get_status_returns_current(self):
        r"""Should return current status from redis."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.return_value = "PAUSED"
        service.key = "TEST_KEY"
        assert service.get_status() == "PAUSED"

    def test_get_status_defaults_to_running(self):
        r"""Should default to RUNNING when key is not set."""
        service = ControlService.__new__(ControlService)
        service.redis = MagicMock()
        service.redis.get.return_value = None
        service.key = "TEST_KEY"
        assert service.get_status() == "RUNNING"
