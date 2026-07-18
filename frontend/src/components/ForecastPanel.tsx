import type { ForecastResponse } from "../types/stock";

export function ForecastPanel({ forecast, disabled, onTrain }: {
  forecast: ForecastResponse | null; disabled: boolean; onTrain: () => void;
}) {
  return <section className="forecast-section">
    <div className="section-heading"><div><p className="eyebrow">Phase 2 · experimental ML</p><h2>Next-day forecast</h2></div>
      <button className="button forecast-button" disabled={disabled} onClick={onTrain}>Train &amp; forecast</button></div>
    {!forecast ? <div className="forecast-empty">Load 100 stored daily records, then train an evaluated forecast.</div> :
      <div className="forecast-card">
        <div className="forecast-primary"><span>Predicted return after {forecast.as_of_date}</span>
          <strong className={forecast.predicted_return_percent >= 0 ? "positive" : "negative"}>{forecast.predicted_return_percent >= 0 ? "+" : ""}{forecast.predicted_return_percent.toFixed(2)}%</strong>
          <p>${forecast.predicted_price.toFixed(2)} · 90% empirical range ${forecast.price_range_low.toFixed(2)}–${forecast.price_range_high.toFixed(2)}</p></div>
        <div className="forecast-metrics">
          <div><span>Probability up</span><strong>{forecast.probability_up_percent.toFixed(1)}%</strong></div>
          <div><span>Walk-forward MAE</span><strong>{forecast.metrics.model_mae_percent.toFixed(2)}%</strong></div>
          <div><span>Zero-return baseline</span><strong>{forecast.metrics.baseline_mae_percent.toFixed(2)}%</strong></div>
          <div><span>Directional accuracy</span><strong>{forecast.metrics.directional_accuracy_percent.toFixed(1)}%</strong></div>
        </div>
        <div className={`baseline-verdict ${forecast.metrics.beats_baseline ? "pass" : "warn"}`}>{forecast.metrics.beats_baseline ? "Model beat the baseline in this backtest." : "Model did not beat the baseline in this backtest."}<span>{forecast.metrics.validation_observations} walk-forward predictions · {forecast.model_name}</span></div>
        <p className="forecast-disclaimer">{forecast.disclaimer} Probability is a model estimate, not a calibrated guarantee.</p>
      </div>}
  </section>;
}
