import pytest

from forecast.core.eval.definitions import EvaluationReport, EvaluationResult
from forecast.kit.eval.analytics import SliceAnalytics


def test_compute_slices():
    """Verify grouping logic and score aggregation."""

    # 1. Create a set of results with mixed tags
    results = [
        # Group 1: Science (Score 0.1)
        EvaluationResult(subject_id="q1", score=0.1, ground_truth=1.0, prediction=0.9, metadata={"tags": ["science"]}),
        # Group 2: Politics (Score 0.5)
        EvaluationResult(subject_id="q2", score=0.5, ground_truth=0.0, prediction=0.5, metadata={"tags": ["politics"]}),
        # Group 3: Both (Score 0.2)
        EvaluationResult(
            subject_id="q3", score=0.2, ground_truth=1.0, prediction=0.8, metadata={"tags": ["science", "politics"]}
        ),
    ]

    # 2. Compute Slices
    slices = SliceAnalytics.compute_slices(results)

    # 3. Validation

    # Expect "tag:science" to include q1 and q3
    # Mean Score: (0.1 + 0.2) / 2 = 0.15
    assert "tag:science" in slices
    report_sci = slices["tag:science"]
    assert report_sci.total_evaluations == 2
    assert report_sci.mean_score == pytest.approx(0.15)

    # Expect "tag:politics" to include q2 and q3
    # Mean Score: (0.5 + 0.2) / 2 = 0.35
    assert "tag:politics" in slices
    report_pol = slices["tag:politics"]
    assert report_pol.total_evaluations == 2
    assert report_pol.mean_score == pytest.approx(0.35)

    # Verify recursive nature (slices of slices NOT implemented yet, but ensure schema holds)
    assert isinstance(slices["tag:science"], EvaluationReport)


def test_compute_slices_empty():
    """Verify empty input handling."""
    slices = SliceAnalytics.compute_slices([])
    assert slices == {}


def test_compute_slices_no_tags():
    """Verify results without tags are ignored."""
    results = [EvaluationResult(subject_id="q1", score=0.0, ground_truth=1.0, prediction=1.0, metadata={})]
    slices = SliceAnalytics.compute_slices(results)
    assert slices == {}
