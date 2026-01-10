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
import os
import tempfile
from datetime import datetime

from forecast.core.schemas.forecast import ForecastOutput
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.kit.eval.replayer import TraceReplayer

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TraceDemo")


def main():
    print("--- 📼 Deterministic Trace Replay Demo ---")

    # 1. Simulate a Live Run
    # In a real scenario, this state comes from `await orchestrator.run(...)`
    logger.info("Simulating live forecast execution...")

    live_state = BaseGraphState(
        subject_id="question-123",
        temporal_context=TemporalContext(reference_time=datetime(2025, 1, 1), is_backtest=True),
        node_reports={
            "ingestion": "Will X happen?",
            "analyst": "Evidence suggests a high probability.",
            "final_forecast": ForecastOutput(
                question_id="question-123",
                confidence=0.8,
                reasoning="Strong bullish signals.",
                structural_trace=["ingestion", "analyst", "final_forecast"],
            ),
        },
    )

    # 2. Serialize (Save Trace)
    # We save this to a file to mimic "Offline" storage
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        trace_path = tmp.name

    logger.info(f"Saving execution trace to: {trace_path}")
    TraceReplayer.save_trace(live_state, trace_path)

    # 3. Offline Replay (Scenario A: Truth = YES)
    logger.info("\n--- Replay A: Ground Truth = YES (1.0) ---")

    replayer = TraceReplayer()

    # We assume 'YES' happened.
    # Expected Brier: (0.8 - 1.0)^2 = 0.04
    result_a = replayer.replay_evaluation(trace_path=trace_path, resolution="YES")

    print(f"Prediction: {0.8}")
    print("Outcome:    YES (1.0)")
    print(f"Brier Score: {result_a.score:.4f}")

    # 4. Offline Replay (Scenario B: Truth = NO)
    logger.info("\n--- Replay B: Ground Truth = NO (0.0) ---")

    # We verify what the score WOULD have been if the outcome was NO.
    # Expected Brier: (0.8 - 0.0)^2 = 0.64
    result_b = replayer.replay_evaluation(trace_path=trace_path, resolution="NO")

    print(f"Prediction: {0.8}")
    print("Outcome:    NO (0.0)")
    print(f"Brier Score: {result_b.score:.4f}")

    # Cleanup
    os.remove(trace_path)
    logger.info("\nTrace file deleted. Demo complete.")


if __name__ == "__main__":
    main()
