import logging

import numpy as np

from forecast.eval.viz import ReliabilityDiagram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CALIBRATION_DEMO")


def main():
    logger.info("--- Generating Synthetic Data ---")
    np.random.seed(42)
    n_samples = 1000

    # 1. Perfectly Calibrated Model (y_prob ~ true prob)
    # If prob is 0.7, we let it be 1 with 70% chance
    y_prob_calibrated = np.random.uniform(0, 1, n_samples)
    y_true_calibrated = np.random.binomial(1, y_prob_calibrated)

    # 2. Overconfident Model (pushes probs to 0 or 1)
    # If prob < 0.5 -> 0.1, if > 0.5 -> 0.9
    y_prob_over = np.where(y_prob_calibrated < 0.5, y_prob_calibrated * 0.5, 0.5 + (y_prob_calibrated - 0.5) * 1.5)
    y_prob_over = np.clip(y_prob_over, 0.01, 0.99)
    # Truth is the same, but predictions are extreme
    y_true_over = y_true_calibrated

    logger.info("--- Computing Reliability Diagrams ---")
    rd = ReliabilityDiagram(n_bins=10)

    # Plot Calibrated
    rd.plot(y_true_calibrated, y_prob_calibrated, save_path="calibrated_plot.png")

    # Plot Overconfident
    rd.plot(y_true_over, y_prob_over, save_path="overconfident_plot.png")

    logger.info("✅ Calibration demos saved to current directory.")


if __name__ == "__main__":
    main()
