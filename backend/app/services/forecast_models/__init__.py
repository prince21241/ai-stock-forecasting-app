from app.services.forecast_models.lightgbm_model import LightGBMForecastModel
from app.services.forecast_models.ridge import RidgeForecastModel

DEFAULT_MODELS = (RidgeForecastModel(), LightGBMForecastModel())
