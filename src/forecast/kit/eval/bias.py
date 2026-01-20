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
Bias Interceptor: Cognitive bias detection for forecasting audit trails.
"""

from typing import Any, Dict

from forecast.core.eval.definitions import EvaluationResult, Evaluator


class BiasInterceptor(Evaluator):
    r"""
    An evaluator that audits reasoning traces for common cognitive biases.

    This evaluator scans both human and AI reasoning for indicators of:
    - Base-Rate Neglect
    - Overconfidence
    - Availability Heuristic
    - Confirmation Bias
    - Anchoring
    """

    COGNITIVE_BIASES = [
        "Base-Rate Neglect",
        "Overconfidence",
        "Availability Heuristic",
        "Confirmation Bias",
        "Anchoring Bias",
        "Sunk Cost Fallacy",
        "Hindsight Bias",
        "Optimism Bias",
        "Pessimism Bias",
        "Status Quo Bias",
        "Framing Effect",
        "Recency Bias"
    ]

    def __init__(self, model: Any):
        self.model = model

    def score(self, prediction: Any, ground_truth: Any) -> float:
        r"""Score is not applicable for bias detection."""
        return 0.0

    async def evaluate_reasoning(self, reasoning: str) -> Dict[str, Any]:
        r"""
        Audits a reasoning trace for cognitive biases.
        """
        prompt = f"""
        You are a Cognitive Bias Auditor specialized in probabilistic forecasting.
        Analyze the following reasoning trace for indicators of any of these biases:
        {", ".join(self.COGNITIVE_BIASES)}

        Reasoning:
        "{reasoning}"

        Return a JSON object with:
        - "detected_biases": [list of bias names]
        - "severity": [0-10]
        - "explanation": "Brief rationale"
        """
        response = await self.model.generate(prompt)
        # In a real impl, we would use the parser here.
        return {"raw_audit": response.text}

    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        r"""Standard evaluation interface."""
        return EvaluationResult(
            subject_id=subject_id,
            score=0.0,
            ground_truth=ground_truth,
            prediction=prediction,
            metadata={"type": "bias_audit"}
        )


__all__ = ["BiasInterceptor"]
