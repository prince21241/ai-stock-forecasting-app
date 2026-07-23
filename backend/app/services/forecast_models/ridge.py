from dataclasses import dataclass

import numpy as np

RIDGE_ALPHA = 1.0


@dataclass(frozen=True)
class RidgeModelState:
    coefficients: np.ndarray
    mean: np.ndarray
    scale: np.ndarray


class RidgeForecastModel:
    name = "ridge_regression_v1"

    def fit(self, features: np.ndarray, targets: np.ndarray) -> RidgeModelState:
        mean = features.mean(axis=0)
        scale = features.std(axis=0)
        scale[scale == 0] = 1
        normalized = (features - mean) / scale
        design = np.column_stack((np.ones(len(normalized)), normalized))
        penalty = np.eye(design.shape[1]) * RIDGE_ALPHA
        penalty[0, 0] = 0
        coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ targets)
        return RidgeModelState(coefficients=coefficients, mean=mean, scale=scale)

    def predict(self, model: RidgeModelState, row: np.ndarray) -> float:
        normalized = np.concatenate(([1.0], (row - model.mean) / model.scale))
        return float(normalized @ model.coefficients)
