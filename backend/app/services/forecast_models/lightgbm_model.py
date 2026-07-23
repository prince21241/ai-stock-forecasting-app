import lightgbm as lgb
import numpy as np


class LightGBMForecastModel:
    name = "lightgbm_v1"

    def fit(self, features: np.ndarray, targets: np.ndarray) -> lgb.LGBMRegressor:
        model = lgb.LGBMRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.05,
            min_child_samples=5,
            random_state=42,
            verbose=-1,
        )
        model.fit(features, targets)
        return model

    def predict(self, model: lgb.LGBMRegressor, row: np.ndarray) -> float:
        return float(model.predict(row.reshape(1, -1))[0])
