from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from app.services.forecast_models.base import WalkForwardResult


@dataclass(frozen=True)
class ReliabilityBin:
    bin_start_percent: float
    bin_end_percent: float
    mean_predicted_percent: float
    observed_frequency_percent: float
    sample_count: int


@dataclass(frozen=True)
class CalibrationResult:
    probability_up_percent: float
    brier_score: float
    method: str
    reliability_bins: tuple[ReliabilityBin, ...]


@dataclass(frozen=True)
class PlattScaler:
    slope: float
    intercept: float

    def predict_proba(self, score: float) -> float:
        return float(1 / (1 + np.exp(-(self.slope * score + self.intercept))))


def _fit_platt(scores: np.ndarray, labels: np.ndarray) -> PlattScaler:
    if len(scores) < 5 or len(np.unique(labels)) < 2:
        return PlattScaler(slope=1.0, intercept=0.0)

    def neg_log_likelihood(params: np.ndarray) -> float:
        slope, intercept = params
        logits = slope * scores + intercept
        logits = np.clip(logits, -30, 30)
        probabilities = 1 / (1 + np.exp(-logits))
        probabilities = np.clip(probabilities, 1e-6, 1 - 1e-6)
        return float(
            -np.sum(labels * np.log(probabilities) + (1 - labels) * np.log(1 - probabilities))
        )

    result = minimize(
        neg_log_likelihood,
        x0=np.array([1.0, 0.0]),
        method="L-BFGS-B",
    )
    if result.success:
        return PlattScaler(slope=float(result.x[0]), intercept=float(result.x[1]))
    return PlattScaler(slope=1.0, intercept=0.0)


def _reliability_bins(
    probabilities: np.ndarray, labels: np.ndarray, bin_count: int = 5
) -> tuple[ReliabilityBin, ...]:
    if len(probabilities) == 0:
        return ()
    edges = np.linspace(0, 1, bin_count + 1)
    bins: list[ReliabilityBin] = []
    for index in range(bin_count):
        upper = edges[index + 1]
        if index < bin_count - 1:
            mask = (probabilities >= edges[index]) & (probabilities < upper)
        else:
            mask = (probabilities >= edges[index]) & (probabilities <= upper)
        count = int(mask.sum())
        if count == 0:
            continue
        bins.append(
            ReliabilityBin(
                bin_start_percent=round(float(edges[index] * 100), 1),
                bin_end_percent=round(float(edges[index + 1] * 100), 1),
                mean_predicted_percent=round(float(probabilities[mask].mean() * 100), 1),
                observed_frequency_percent=round(float(labels[mask].mean() * 100), 1),
                sample_count=count,
            )
        )
    return tuple(bins)


def calibrate_walk_forward(
    evaluation: WalkForwardResult, latest_score: float
) -> CalibrationResult:
    labels = (evaluation.actuals > 0).astype(float)
    scaler = _fit_platt(evaluation.predictions, labels)
    calibrated = np.array([scaler.predict_proba(score) for score in evaluation.predictions])
    brier = float(np.mean((calibrated - labels) ** 2))
    return CalibrationResult(
        probability_up_percent=round(scaler.predict_proba(latest_score) * 100, 1),
        brier_score=round(brier, 4),
        method="platt",
        reliability_bins=_reliability_bins(calibrated, labels),
    )
