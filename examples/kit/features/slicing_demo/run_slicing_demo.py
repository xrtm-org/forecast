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
from typing import List

from xrtm.forecast.core.eval.definitions import EvaluationReport, EvaluationResult
from xrtm.forecast.kit.eval.analytics import SliceAnalytics

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("SlicingDemo")


def print_report_table(title: str, report: EvaluationReport):
    r"""Helper to format and print an evaluation report with its metadata slices."""
    print(f"\n[{title}]")
    print(f"  > Brier Score: {report.mean_score:.4f} (N={report.total_evaluations})")

    if report.slices:
        print("  > Slices:")
        print(f"    {'Tag':<15} | {'Score':<8} | {'Count'}")
        print("    " + "-" * 35)
        for tag, sub_report in report.slices.items():
            print(f"    {tag:<15} | {sub_report.mean_score:<8.4f} | {sub_report.total_evaluations}")


def main():
    print("--- 🍰 Metadata Slicing Demo ---")

    # 1. Simulate Results from a Backtest
    # Imagine we ran a backtest on 100 questions covering various topics

    results: List[EvaluationResult] = []

    # Group A: Politics (Harder, average score 0.45)
    for i in range(5):
        results.append(
            EvaluationResult(
                subject_id=f"pol-{i}",
                score=0.45,
                ground_truth=1,
                prediction=0.55,
                metadata={"tags": ["politics", "us_news"]},
            )
        )

    # Group B: Science (Easier, average score 0.15)
    for i in range(5):
        results.append(
            EvaluationResult(
                subject_id=f"sci-{i}",
                score=0.15,
                ground_truth=0,
                prediction=0.15,
                metadata={"tags": ["science", "tech"]},
            )
        )

    # Group C: Crypto (Very Noisy, average score 0.60)
    for i in range(5):
        results.append(
            EvaluationResult(
                subject_id=f"cry-{i}", score=0.60, ground_truth=1, prediction=0.4, metadata={"tags": ["crypto", "tech"]}
            )
        )

    # 2. Run Analytics
    logger.info("Computing slices...")

    # This logic matches what happens inside BacktestRunner.run()
    slices = SliceAnalytics.compute_slices(results)

    global_score = sum(r.score for r in results) / len(results)

    report = EvaluationReport(
        metric_name="Brier Score",
        mean_score=global_score,
        total_evaluations=len(results),
        results=results,
        slices=slices,
    )

    # 3. Display Report
    print_report_table("Global Backtest Report", report)


if __name__ == "__main__":
    main()
