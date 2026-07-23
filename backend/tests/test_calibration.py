import numpy as np

from app.services.forecast_calibration import calibrate_walk_forward
from app.services.forecast_models.base import WalkForwardResult


def test_platt_calibration_returns_probability_and_bins() -> None:
    predictions = np.array([0.02, -0.01, 0.03, -0.02, 0.015, -0.005, 0.01, -0.015])
    actuals = np.array([0.025, -0.005, 0.04, -0.01, 0.02, 0.0, 0.015, -0.02])
    evaluation = WalkForwardResult(predictions, actuals)
    result = calibrate_walk_forward(evaluation, 0.012)
    assert 0 <= result.probability_up_percent <= 100
    assert 0 <= result.brier_score <= 1
    assert result.method == "platt"
    assert len(result.reliability_bins) >= 1
