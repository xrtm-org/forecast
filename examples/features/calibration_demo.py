import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from forecast.eval.runner import BacktestDataset, BacktestInstance, BacktestRunner
from forecast.graph.orchestrator import Orchestrator
from forecast.schemas.forecast import ForecastQuestion, ForecastResolution, MetadataBase
from forecast.schemas.graph import BaseGraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CALIBRATION_DEMO")


class MockOrchestrator(Orchestrator):
    def __init__(self, confidence: float):
        self.confidence = confidence

    async def run(
        self,
        state: BaseGraphState,
        entry_node: str = "ingestion",
        on_progress: Optional[Any] = None,
        stopwatch: Optional[Any] = None,
    ) -> BaseGraphState:
        # Simulate agent always outputting fixed confidence
        state.node_reports["final"] = {"confidence": self.confidence}
        # Simulate latency
        state.latencies["mock_node"] = 0.05
        return state


async def main():
    logger.info("--- v0.2.1 Calibration Demo ---")

    # 1. Create a dataset where Agent matches Ground Truth (Perfect Calibration)
    items = []
    for i in range(10):
        items.append(
            BacktestInstance(
                question=ForecastQuestion(id=f"q{i}", title="Demo", metadata=MetadataBase(market_type="BINARY")),
                resolution=ForecastResolution(question_id=f"q{i}", outcome="1.0"),
                reference_time=datetime(2025, 1, 1),
            )
        )

    dataset = BacktestDataset(items=items)

    # 2. Run with Perfect Predictor (Conf=1.0, Outcome=1.0)
    logger.info("Running Perfect Predictor (Conf=1.0)...")
    runner = BacktestRunner(orchestrator=MockOrchestrator(confidence=1.0))
    report = await runner.run(dataset)

    logger.info(f"Brier Score: {report.mean_score:.4f} (Expected 0.0)")
    logger.info(f"ECE: {report.summary_statistics['ece']:.4f} (Expected 0.0)")

    # 3. Export Data for Research (Simulation)
    # In a real script, you'd save to a path. For this demo, we print the structure.
    print("\n--- JSON Export Structure ---")
    print(report.model_dump_json(indent=2))
    logger.info("Reliability data printed to console (No Root I/O).")


if __name__ == "__main__":
    asyncio.run(main())
