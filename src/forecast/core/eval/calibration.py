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

import pickle
from pathlib import Path
from typing import List, Union

import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.linear_model import LogisticRegression


class PlattScaler(BaseModel):
    r"""
    A probabilistic calibrator using Platt Scaling (Logistic Regression).

    This scaler transforms raw, potentially uncalibrated probabilities (logits or probs)
    into calibrated probabilities that match the empirical frequency of the positive class.

    Attributes:
        a (`float`): The slope parameter (scaling factor). a > 1 implies extremization.
        b (`float`): The intercept parameter (bias correction).
        fitted (`bool`): Whether the scaler has been fitted.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    a: float = 1.0
    b: float = 0.0
    fitted: bool = False

    def fit(self, y_true: List[int], y_prob: List[float]) -> "PlattScaler":
        r"""
        Fits the scaler to a dataset of predictions and outcomes.

        Args:
            y_true (`List[int]`):
                Ground truth labels (0 or 1).
            y_prob (`List[float]`):
                Raw predicted probabilities from the agent [0.0, 1.0].
                We convert these to logits internally before fitting.

        Returns:
            `PlattScaler`: The fitted instance.
        """
        # 1. Convert probs to logits (clipping to avoid inf)
        eps = 1e-15
        p = np.clip(y_prob, eps, 1 - eps)
        logits = np.log(p / (1 - p)).reshape(-1, 1)

        # 2. Fit Logistic Regression
        # Use C=infinite (large float) to emulate no regularization (penalty=None deprecation fix)
        # Using l2 with huge C is standard replacement.
        clf = LogisticRegression(C=1e10, solver="lbfgs")
        clf.fit(logits, y_true)

        # 3. Extract parameters
        # sklearn form: logit(p) = coef * x + intercept
        self.a = float(clf.coef_[0][0])
        self.b = float(clf.intercept_[0])
        self.fitted = True

        return self

    def transform(self, y_prob: Union[float, List[float]]) -> Union[float, List[float]]:
        r"""
        Calibrates a raw probability using the fitted parameters.

        Formula: p_calibrated = sigmoid(a * logit(p) + b)

        Args:
            y_prob (`float` or `List[float]`): Raw probability [0.0, 1.0].

        Returns:
            Calibrated probability or list of probabilities.
        """
        if not self.fitted:
            return y_prob

        # Handle scalar input
        is_scalar = isinstance(y_prob, (float, int))
        y_prob_arr = np.array([y_prob]) if is_scalar else np.array(y_prob)

        # Logit transform
        eps = 1e-15
        p = np.clip(y_prob_arr, eps, 1 - eps)
        logits = np.log(p / (1 - p))

        # Linear scaling + Sigmoid
        scaled_logits = self.a * logits + self.b
        p_calib = 1.0 / (1.0 + np.exp(-scaled_logits))

        if is_scalar:
            return float(p_calib[0])
        return p_calib.tolist()

    def save(self, path: Union[str, Path]) -> None:
        r"""
        Saves the fitted scaler to a pickle file.
        """
        model_data = {"a": self.a, "b": self.b, "fitted": self.fitted}
        with open(path, "wb") as f:
            pickle.dump(model_data, f)

    def load(self, path: Union[str, Path]) -> "PlattScaler":
        r"""
        Loads the scaler from a pickle file.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.a = data["a"]
        self.b = data["b"]
        self.fitted = data["fitted"]
        return self

        self.a = data["a"]
        self.b = data["b"]
        self.fitted = data["fitted"]
        return self
