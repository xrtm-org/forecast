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
The Researcher Kit: High-level components for forecasting pipelines.

This module provides production-ready agents, topologies, and evaluators
for building institutional-grade forecasting systems.
"""

# Topologies
# Evaluation (Migrated to xrtm-eval)
from xrtm.eval.kit.eval.epistemic_evaluator import EpistemicEvaluator
from xrtm.eval.kit.eval.resilience import AdversarialInjector, GullibilityReport

from xrtm.forecast.kit.agents.fact_checker import FactCheckerAgent

# Agents
from xrtm.forecast.kit.agents.red_team import RedTeamAgent

# Sentinel
from xrtm.forecast.kit.sentinel import PollingDriver, SentinelDriver, TriggerRules
from xrtm.forecast.kit.topologies import (
    RecursiveConsensus,
    create_ivw_aggregator,
    create_simple_aggregator,
)

__all__ = [
    # Topologies
    "RecursiveConsensus",
    "create_ivw_aggregator",
    "create_simple_aggregator",
    # Agents
    "RedTeamAgent",
    "FactCheckerAgent",
    # Evaluation
    "AdversarialInjector",
    "GullibilityReport",
    "EpistemicEvaluator",
    # Sentinel
    "PollingDriver",
    "SentinelDriver",
    "TriggerRules",
]
