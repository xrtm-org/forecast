import logging
from typing import Dict, List

from forecast.core.eval.definitions import EvaluationReport, EvaluationResult
from forecast.kit.eval.metrics import ExpectedCalibrationErrorEvaluator

logger = logging.getLogger(__name__)


class SliceAnalytics:
    r"""
    Advanced analytics for partitioning evaluation results by metadata.

    This utility enables "Slicing" - the ability to look at model performance
    on specific sub-sets of the data (e.g., "Performance on Tag:Science" vs "Tag:Politics").
    """

    @staticmethod
    def compute_slices(results: List[EvaluationResult]) -> Dict[str, EvaluationReport]:
        r"""
        Groups results by tags and computes a sub-report for each group.

        Args:
            results: The full list of evaluation results.

        Returns:
            A dictionary mapping slice names (e.g., "tag:science") to their reports.
        """
        slices: Dict[str, List[EvaluationResult]] = {}

        # 1. Group by keys
        for res in results:
            tags = res.metadata.get("tags", [])
            if not tags:
                continue

            for tag in tags:
                key = f"tag:{tag}"
                if key not in slices:
                    slices[key] = []
                slices[key].append(res)

        # 2. Compute Reports for each slice
        reports: Dict[str, EvaluationReport] = {}

        for slice_key, slice_results in slices.items():
            count = len(slice_results)
            if count == 0:
                continue

            total_score = sum(r.score for r in slice_results)
            mean_score = total_score / count

            # ECE for this slice
            ece_evaluator = ExpectedCalibrationErrorEvaluator()
            try:
                ece_score, bins = ece_evaluator.compute_calibration_data(slice_results)
            except Exception as e:
                logger.warning(f"Failed to compute ECE for slice {slice_key}: {e}")
                ece_score = 0.0
                bins = None

            reports[slice_key] = EvaluationReport(
                metric_name="Slice Brier",  # Generic name
                mean_score=mean_score,
                total_evaluations=count,
                results=slice_results,  # Include subset results
                reliability_bins=bins,
                summary_statistics={"ece": ece_score},
            )

        return reports
