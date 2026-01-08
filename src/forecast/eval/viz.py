# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ReliabilityCurveData:
    prob_pred: np.ndarray
    prob_true: np.ndarray
    ece: float


def compute_calibration_curve(y_true: List[int], y_prob: List[float], n_bins: int = 10) -> ReliabilityCurveData:
    """
    Computes the calibration curve (reliability diagram) data.

    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted probabilities for the positive class.
        n_bins: Number of bins for discretization.

    Returns:
        ReliabilityCurveData with bin coordinates and ECE score.
    """
    # Use numpy for efficient binning
    y_true_arr = np.array(y_true)
    y_prob_arr = np.array(y_prob)

    if len(y_prob_arr) == 0:
        return ReliabilityCurveData(np.array([]), np.array([]), 0.0)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    binids = np.digitize(y_prob_arr, bins) - 1

    # Handle the edge case where probability is exactly 1.0
    # digitize returns len(bins) for values >= bins[-1] if not right=True (default is left-inclusive)
    # Ensure all indices are within [0, n_bins-1]
    binids = np.clip(binids, 0, n_bins - 1)

    bin_true = []
    bin_pred = []
    bin_total = []

    ece = 0.0
    total_samples = len(y_prob_arr)

    for i in range(n_bins):
        mask = binids == i
        if not np.any(mask):
            continue

        count = np.sum(mask)
        fraction_true = np.mean(y_true_arr[mask])
        mean_prob = np.mean(y_prob_arr[mask])

        bin_true.append(fraction_true)
        bin_pred.append(mean_prob)
        bin_total.append(count)

        # Expected Calibration Error (ECE)
        ece += (count / total_samples) * np.abs(fraction_true - mean_prob)

    return ReliabilityCurveData(prob_pred=np.array(bin_pred), prob_true=np.array(bin_true), ece=ece)


def plot_reliability_diagram(
    data: ReliabilityCurveData, title: str = "Reliability Diagram", save_path: Optional[str] = None
) -> Any:
    """
    Plots the reliability diagram using Matplotlib/Seaborn.
    Safely handles missing dependencies.
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.error("Visualization libraries not installed. Run `pip install xrtm-forecast[viz]`.")
        return None

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(6, 6))

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], "k:", label="Perfectly Calibrated")

    # Reliability curve
    ax.plot(data.prob_pred, data.prob_true, "s-", label=f"Model (ECE={data.ece:.3f})")

    # Formatting
    ax.set_ylabel("Fraction of Positives")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylim((-0.05, 1.05))
    ax.set_xlim((-0.05, 1.05))
    ax.set_title(title)
    ax.legend(loc="lower right")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        logger.info(f"Reliability diagram saved to {save_path}")

    return fig


class ReliabilityDiagram:
    """
    Institutional wrapper for calibration analysis.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    def compute(self, y_true: List[int], y_prob: List[float]) -> ReliabilityCurveData:
        return compute_calibration_curve(y_true, y_prob, self.n_bins)

    def plot(self, y_true: List[int], y_prob: List[float], save_path: Optional[str] = None) -> Any:
        data = self.compute(y_true, y_prob)
        return plot_reliability_diagram(data, save_path=save_path)
