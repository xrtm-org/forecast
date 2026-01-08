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
Standardized exception definitions for the xrtm-forecast platform.

This module provides a unified hierarchy of error classes that ensure consistent
unwinding and reporting across all platform components, from inference providers
to autonomous agents.
"""


class ForecastError(Exception):
    r"""Base class for all xrtm-forecast exceptions."""

    pass


class ProviderError(ForecastError):
    r"""
    Raised when an inference provider fails to process a request.

    This can occur due to API outages, content filtering, or rate limits.
    """

    pass


class SkillError(ForecastError):
    r"""
    Raised when a skill execution fails.

    Indicates that a high-level agent capability encountered an unrecoverable
    error during its internal process.
    """

    pass


class ConfigurationError(ForecastError):
    r"""
    Raised when the platform is misconfigured.

    Typically encountered during initialization when API keys are missing
    or environment variables are invalid.
    """

    pass


class GraphError(ForecastError):
    r"""
    Raised when the orchestrator encounters a structural or logic error.

    Used for cyclic dependencies, unknown nodes, or state-machine failures.
    """

    pass


__all__ = [
    "ForecastError",
    "ProviderError",
    "SkillError",
    "ConfigurationError",
    "GraphError",
]
