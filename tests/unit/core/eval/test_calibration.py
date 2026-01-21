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

r"""Unit tests for forecast.core.eval.calibration."""

from forecast.core.eval.calibration import BetaScaler, PlattScaler


class TestPlattScaler:
    r"""Tests for the PlattScaler calibration class."""

    def test_default_params(self):
        r"""Should have default params a=1, b=0."""
        scaler = PlattScaler()
        assert scaler.a == 1.0
        assert scaler.b == 0.0
        assert scaler.fitted is False

    def test_transform_not_fitted(self):
        r"""Should return input unchanged when not fitted."""
        scaler = PlattScaler()
        result = scaler.transform(0.7)
        assert result == 0.7

    def test_transform_not_fitted_list(self):
        r"""Should return input list unchanged when not fitted."""
        scaler = PlattScaler()
        result = scaler.transform([0.3, 0.5, 0.8])
        assert result == [0.3, 0.5, 0.8]

    def test_fit_sets_params(self):
        r"""Should set a, b params after fitting."""
        scaler = PlattScaler()
        y_true = [0, 0, 1, 1, 1, 1]
        y_prob = [0.2, 0.3, 0.6, 0.7, 0.8, 0.9]

        scaler.fit(y_true, y_prob)

        assert scaler.fitted is True
        assert isinstance(scaler.a, float)
        assert isinstance(scaler.b, float)

    def test_transform_scalar(self):
        r"""Should transform single probability."""
        scaler = PlattScaler()
        scaler.fit([0, 0, 1, 1], [0.2, 0.4, 0.6, 0.8])

        result = scaler.transform(0.5)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_transform_list(self):
        r"""Should transform list of probabilities."""
        scaler = PlattScaler()
        scaler.fit([0, 0, 1, 1], [0.2, 0.4, 0.6, 0.8])

        result = scaler.transform([0.3, 0.5, 0.7])

        assert isinstance(result, list)
        assert len(result) == 3
        for r in result:
            assert 0.0 <= r <= 1.0

    def test_save_and_load(self, tmp_path):
        r"""Should save and load scaler state."""
        scaler = PlattScaler()
        scaler.fit([0, 0, 1, 1], [0.2, 0.4, 0.6, 0.8])

        filepath = tmp_path / "scaler.pkl"
        scaler.save(filepath)

        new_scaler = PlattScaler()
        new_scaler.load(filepath)

        assert new_scaler.a == scaler.a
        assert new_scaler.b == scaler.b
        assert new_scaler.fitted is True


class TestBetaScaler:
    r"""Tests for the BetaScaler calibration class."""

    def test_default_params(self):
        r"""Should have default params a=1, b=1, c=0."""
        scaler = BetaScaler()
        assert scaler.a == 1.0
        assert scaler.b == 1.0
        assert scaler.c == 0.0
        assert scaler.fitted is False

    def test_transform_not_fitted(self):
        r"""Should return input unchanged when not fitted."""
        scaler = BetaScaler()
        result = scaler.transform(0.7)
        assert result == 0.7

    def test_transform_not_fitted_list(self):
        r"""Should return input list unchanged when not fitted."""
        scaler = BetaScaler()
        result = scaler.transform([0.3, 0.5, 0.8])
        assert result == [0.3, 0.5, 0.8]

    def test_fit_sets_params(self):
        r"""Should set a, b, c params after fitting."""
        scaler = BetaScaler()
        y_true = [0, 0, 1, 1, 1, 1]
        y_prob = [0.2, 0.3, 0.6, 0.7, 0.8, 0.9]

        scaler.fit(y_true, y_prob)

        assert scaler.fitted is True
        assert isinstance(scaler.a, float)
        assert isinstance(scaler.b, float)
        assert isinstance(scaler.c, float)

    def test_transform_scalar(self):
        r"""Should transform single probability."""
        scaler = BetaScaler()
        scaler.fit([0, 0, 1, 1], [0.2, 0.4, 0.6, 0.8])

        result = scaler.transform(0.5)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_transform_list(self):
        r"""Should transform list of probabilities."""
        scaler = BetaScaler()
        scaler.fit([0, 0, 1, 1], [0.2, 0.4, 0.6, 0.8])

        result = scaler.transform([0.3, 0.5, 0.7])

        assert isinstance(result, list)
        assert len(result) == 3
        for r in result:
            assert 0.0 <= r <= 1.0

    def test_edge_probabilities(self):
        r"""Should handle edge probabilities (near 0 or 1)."""
        scaler = BetaScaler()
        scaler.fit([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])

        # Test extreme values - should not crash due to clipping
        result = scaler.transform([0.001, 0.999])

        assert isinstance(result, list)
        assert len(result) == 2
