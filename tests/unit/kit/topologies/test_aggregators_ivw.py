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

r"""Tests for the local inverse-variance aggregator (no xrtm-eval dependency)."""

import pathlib

import pytest

import xrtm.forecast.kit.topologies.aggregators as aggregators
from xrtm.forecast.kit.topologies.aggregators import (
    _output_variance,
    inverse_variance_weighting,
)


class _Output:
    def __init__(self, confidence=None, uncertainty=None, interval=None):
        self.confidence = confidence
        self.uncertainty = uncertainty
        self.confidence_interval = interval


class _Interval:
    low = 0.2
    high = 0.6


def test_ivw_weights_low_uncertainty_more():
    outputs = [_Output(confidence=0.2, uncertainty=0.01), _Output(confidence=0.8, uncertainty=0.25)]
    mean, variance = inverse_variance_weighting(outputs)
    assert mean == pytest.approx((0.2 * 100 + 0.8 * 4) / 104)
    assert variance == pytest.approx(1 / 104)


def test_ivw_without_uncertainty_is_the_mean():
    mean, variance = inverse_variance_weighting([_Output(confidence=0.2), _Output(confidence=0.8)])
    assert mean == pytest.approx(0.5)
    assert variance == pytest.approx(0.5)


def test_ivw_derives_variance_from_interval():
    assert _output_variance(_Output(confidence=0.4, interval=_Interval())) == pytest.approx(((0.6 - 0.2) / 3.92) ** 2)


def test_ivw_empty_is_neutral():
    assert inverse_variance_weighting([]) == (0.5, 1.0)


def test_aggregator_module_has_no_eval_dependency():
    # Layering: /kit must not import xrtm.eval (and the old cross-package call
    # also crashed with a signature mismatch).
    source = pathlib.Path(aggregators.__file__).read_text(encoding="utf-8")
    assert "xrtm.eval" not in source
