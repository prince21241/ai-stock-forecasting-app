from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class WalkForwardResult:
    predictions: np.ndarray
    actuals: np.ndarray

    @property
    def model_mae(self) -> float:
        return float(np.mean(np.abs(self.actuals - self.predictions)))

    @property
    def baseline_mae(self) -> float:
        return float(np.mean(np.abs(self.actuals)))

    @property
    def directional_accuracy(self) -> float:
        return float(np.mean(np.sign(self.predictions) == np.sign(self.actuals)))

    @property
    def errors(self) -> np.ndarray:
        return self.actuals - self.predictions


class ForecastModel(Protocol):
    name: str

    def fit(self, features: np.ndarray, targets: np.ndarray) -> object: ...

    def predict(self, model: object, row: np.ndarray) -> float: ...


def walk_forward_evaluate(
    model: ForecastModel,
    features: np.ndarray,
    targets: np.ndarray,
    minimum_training_rows: int,
) -> WalkForwardResult:
    predictions: list[float] = []
    actuals: list[float] = []
    for index in range(minimum_training_rows, len(targets)):
        fitted = model.fit(features[:index], targets[:index])
        predictions.append(model.predict(fitted, features[index]))
        actuals.append(float(targets[index]))
    return WalkForwardResult(
        np.asarray(predictions, dtype=float),
        np.asarray(actuals, dtype=float),
    )
