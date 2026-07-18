import type { ForecastResponse } from "../types/stock";

export function ForecastPanel({ forecast, history, disabled, onTrain }: {
  forecast: ForecastResponse | null; history: ForecastResponse[];
  disabled: boolean; onTrain: () => void;
}) {
  return <section className="forecast-section">
    <div className="section-heading"><div><p className="eyebrow">Phase 2 · experimental ML</p><h2>Next-day forecast</h2></div>
      <button className="button forecast-button" disabled={disabled} onClick={onTrain}>Train &amp; forecast</button></div>
    {!forecast ? <div className="forecast-empty">Load 100 stored daily records, then train an evaluated forecast.</div> :
      <div className="forecast-card">
        <div className={`forecast-primary ${forecast.signal_status === "no_signal" ? "muted" : ""}`}>
          <span>{forecast.signal_status === "qualified" ? "Qualified experimental signal" : "No qualified signal"} · predicted return after {forecast.as_of_date}</span>
          <strong className={forecast.predicted_return_percent >= 0 ? "positive" : "negative"}>{forecast.predicted_return_percent >= 0 ? "+" : ""}{forecast.predicted_return_percent.toFixed(2)}%</strong>
          <p>${forecast.predicted_price.toFixed(2)} · 90% empirical range ${forecast.price_range_low.toFixed(2)}–${forecast.price_range_high.toFixed(2)}</p></div>
        <div className="forecast-metrics">
          <div><span>Probability up</span><strong>{forecast.probability_up_percent.toFixed(1)}%</strong></div>
          <div><span>Walk-forward MAE</span><strong>{forecast.metrics.model_mae_percent.toFixed(2)}%</strong></div>
          <div><span>Zero-return baseline</span><strong>{forecast.metrics.baseline_mae_percent.toFixed(2)}%</strong></div>
          <div><span>Directional accuracy</span><strong>{forecast.metrics.directional_accuracy_percent.toFixed(1)}%</strong></div>
        </div>
        <div className={`baseline-verdict ${forecast.signal_status === "qualified" ? "pass" : "warn"}`}>
          {forecast.signal_status === "qualified" ? "Quality gate passed: baseline beaten with at least 55% directional accuracy." : "No signal: the model did not pass the baseline and directional-accuracy quality gate."}
          <span>{forecast.metrics.validation_observations} walk-forward predictions · {forecast.model_name}</span></div>
        <p className="forecast-disclaimer">{forecast.disclaimer} Probability is a model estimate, not a calibrated guarantee.</p>
      </div>}
    {history.length > 0 && <div className="forecast-history"><h3>Recent forecast runs</h3>
      <div className="forecast-history-list">{history.map((run) => <div key={run.id ?? run.trained_at}>
        <span>{new Date(run.trained_at).toLocaleString()}</span>
        <strong>{run.predicted_return_percent >= 0 ? "+" : ""}{run.predicted_return_percent.toFixed(2)}%</strong>
        <em className={run.signal_status}>{run.signal_status === "qualified" ? "Qualified" : "No signal"}</em>
      </div>)}</div></div>}
  </section>;
}
