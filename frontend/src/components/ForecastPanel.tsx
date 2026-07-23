import type { ForecastResponse, HorizonForecast, ReliabilityBin } from "../types/stock";

function formatModelName(name: string): string {
  return name.replaceAll("_", " ");
}

function formatFeatureSet(featureSet?: string): string {
  return featureSet === "with_sentiment" ? "with sentiment" : "price only";
}

function horizonValue(horizon: HorizonForecast): string {
  if (horizon.horizon === "volatility") {
    return horizon.predicted_volatility_percent != null
      ? `${horizon.predicted_volatility_percent.toFixed(2)}%`
      : "—";
  }
  if (horizon.predicted_return_percent == null) return "—";
  const prefix = horizon.predicted_return_percent >= 0 ? "+" : "";
  return `${prefix}${horizon.predicted_return_percent.toFixed(2)}%`;
}

function ReliabilityDiagram({ bins }: { bins: ReliabilityBin[] }) {
  if (!bins.length) {
    return <p className="calibration-empty">Not enough walk-forward samples to chart calibration bins.</p>;
  }
  return <div className="reliability-chart" aria-label="Probability calibration reliability diagram">
    {bins.map((bin) => {
      const predicted = Math.max(bin.mean_predicted_percent, 4);
      const observed = Math.max(bin.observed_frequency_percent, 4);
      return <div key={`${bin.bin_start_percent}-${bin.bin_end_percent}`} className="reliability-bin">
        <span>{bin.bin_start_percent}–{bin.bin_end_percent}%</span>
        <div className="reliability-bars">
          <div className="predicted" style={{ height: `${predicted}%` }} title={`Predicted ${bin.mean_predicted_percent.toFixed(1)}%`} />
          <div className="observed" style={{ height: `${observed}%` }} title={`Observed ${bin.observed_frequency_percent.toFixed(1)}%`} />
        </div>
        <em>n={bin.sample_count}</em>
      </div>;
    })}
    <div className="reliability-legend"><span><i className="predicted" /> Predicted</span><span><i className="observed" /> Observed</span></div>
  </div>;
}

export function ForecastPanel({ forecast, history, disabled, onTrain }: {
  forecast: ForecastResponse | null; history: ForecastResponse[];
  disabled: boolean; onTrain: () => void;
}) {
  const sentiment = forecast?.sentiment_comparison;
  const calibration = forecast?.calibration;
  const horizons = forecast?.horizons ?? [];
  const modelComparison = forecast?.model_comparison ?? [];

  return <section className="forecast-section">
    <div className="section-heading"><div><p className="eyebrow">Phase 2 · experimental ML</p><h2>Multi-horizon forecast</h2></div>
      <button className="button forecast-button" disabled={disabled} onClick={onTrain}>Train &amp; forecast</button></div>
    {!forecast ? <div className="forecast-empty">Load 100 stored daily records, then train evaluated 1d/5d/20d forecasts with sentiment comparison and calibrated probabilities.</div> :
      <div className="forecast-card">
        <div className={`forecast-primary ${forecast.signal_status === "no_signal" ? "muted" : ""}`}>
          <span>{forecast.signal_status === "qualified" ? "Qualified 1-day signal" : "No qualified 1-day signal"} · {formatModelName(forecast.model_name)} · after {forecast.as_of_date}</span>
          <strong className={forecast.predicted_return_percent >= 0 ? "positive" : "negative"}>{forecast.predicted_return_percent >= 0 ? "+" : ""}{forecast.predicted_return_percent.toFixed(2)}%</strong>
          <p>${forecast.predicted_price.toFixed(2)} · calibrated P(up) {forecast.probability_up_percent.toFixed(1)}% · range ${forecast.price_range_low.toFixed(2)}–${forecast.price_range_high.toFixed(2)}</p></div>
        <div className="forecast-metrics">
          <div><span>Calibrated P(up)</span><strong>{forecast.probability_up_percent.toFixed(1)}%</strong></div>
          <div><span>Walk-forward MAE</span><strong>{forecast.metrics.model_mae_percent.toFixed(2)}%</strong></div>
          <div><span>Brier score</span><strong>{(forecast.metrics.brier_score ?? calibration?.brier_score ?? 0).toFixed(3)}</strong></div>
          <div><span>Directional accuracy</span><strong>{forecast.metrics.directional_accuracy_percent.toFixed(1)}%</strong></div>
        </div>
        {sentiment?.available && <div className="sentiment-comparison">
          <h3>Sentiment feature comparison</h3>
          <div className="sentiment-comparison-grid">
            <div><span>Price only MAE</span><strong>{sentiment.price_only_mae_percent?.toFixed(2) ?? "—"}%</strong></div>
            <div><span>With sentiment MAE</span><strong>{sentiment.with_sentiment_mae_percent?.toFixed(2) ?? "—"}%</strong></div>
            <div><span>Selected features</span><strong>{formatFeatureSet(sentiment.selected_feature_set)}</strong></div>
            <div><span>Sentiment helps?</span><strong>{sentiment.sentiment_improves_mae ? "Yes" : "No"}</strong></div>
          </div>
        </div>}
        {!sentiment?.available && <div className="forecast-feature-note">Price-only features used because news sentiment was unavailable for this run.</div>}
        {modelComparison.length > 0 && <div className="model-comparison">
          <h3>Model comparison</h3>
          <div className="model-comparison-table">
            <div className="model-comparison-head">
              <span>Model</span><span>Features</span><span>MAE</span><span>Status</span>
            </div>
            {modelComparison.map((entry) => <div key={`${entry.model_name}-${entry.feature_set ?? "price_only"}`} className={entry.selected ? "selected" : ""}>
              <span>{formatModelName(entry.model_name)}{entry.selected ? " · selected" : ""}</span>
              <span>{formatFeatureSet(entry.feature_set)}</span>
              <span>{entry.model_mae_percent.toFixed(2)}%</span>
              <em className={entry.signal_status}>{entry.signal_status === "qualified" ? "Qualified" : "No signal"}</em>
            </div>)}
          </div>
        </div>}
        {calibration && <div className="calibration-section">
          <h3>Probability calibration ({calibration.method})</h3>
          <p className="calibration-copy">When the model assigns higher up-probability, walk-forward outcomes should rise with it. Lower Brier score is better.</p>
          <ReliabilityDiagram bins={calibration.reliability_bins} />
        </div>}
        {horizons.length > 0 && <div className="horizon-section">
          <h3>Horizon forecasts</h3>
          <div className="horizon-grid">
            {horizons.map((horizon) => <div key={horizon.horizon} className={`horizon-card ${horizon.signal_status}`}>
              <span>{horizon.label}</span>
              <strong>{horizonValue(horizon)}</strong>
              {horizon.predicted_price != null && horizon.horizon !== "volatility" && <p>${horizon.predicted_price.toFixed(2)}</p>}
              {horizon.probability_up_percent != null && <p>P(up) {horizon.probability_up_percent.toFixed(1)}%</p>}
              {horizon.metrics && <em>{horizon.signal_status === "qualified" ? "Qualified" : horizon.signal_status === "insufficient_data" ? "Insufficient data" : "No signal"} · MAE {horizon.metrics.model_mae_percent.toFixed(2)}%</em>}
            </div>)}
          </div>
        </div>}
        <div className={`baseline-verdict ${forecast.signal_status === "qualified" ? "pass" : "warn"}`}>
          {forecast.signal_status === "qualified" ? "1-day quality gate passed: baseline beaten with at least 55% directional accuracy." : "No 1-day signal: the selected model did not pass the baseline and directional-accuracy quality gate."}
          <span>{forecast.metrics.validation_observations} walk-forward predictions · {formatModelName(forecast.model_name)}</span></div>
        <p className="forecast-disclaimer">{forecast.disclaimer}</p>
      </div>}
    {history.length > 0 && <div className="forecast-history"><h3>Recent forecast runs</h3>
      <div className="forecast-history-list">{history.map((run) => <div key={run.id ?? run.trained_at}>
        <span>{new Date(run.trained_at).toLocaleString()}</span>
        <strong>{run.predicted_return_percent >= 0 ? "+" : ""}{run.predicted_return_percent.toFixed(2)}%</strong>
        <em className={run.signal_status}>{run.signal_status === "qualified" ? "Qualified" : "No signal"}</em>
      </div>)}</div></div>}
  </section>;
}
