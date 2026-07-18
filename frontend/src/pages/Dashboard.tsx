import { useState } from "react";
import { loadStockData, synchronizeStock, trainForecast } from "../api/stocks";
import { ErrorMessage } from "../components/ErrorMessage";
import { Header } from "../components/Header";
import { LoadingState } from "../components/LoadingState";
import { StockSearch } from "../components/StockSearch";
import { StockChart } from "../components/StockChart";
import { SummaryCards } from "../components/SummaryCards";
import { ForecastPanel } from "../components/ForecastPanel";
import type { ForecastResponse, StockListResponse } from "../types/stock";

export function Dashboard() {
  const [symbol, setSymbol] = useState("AAPL");
  const [result, setResult] = useState<StockListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);

  async function loadData(target = symbol) {
    const data = await loadStockData(target.trim());
    setResult(data);
    return data;
  }

  async function run(action: "sync" | "load") {
    setLoading(true); setError(""); setSuccess("");
    try {
      const target = symbol.trim();
      if (action === "sync") {
        const sync = await synchronizeStock(target);
        await loadData(sync.symbol);
        setSuccess(`${sync.symbol} synchronized: ${sync.inserted_or_updated_records} records stored or updated.`);
      } else {
        const data = await loadData(target);
        setSuccess(`${data.count} stored ${data.symbol} records loaded${data.cached ? " from cache" : ""}.`);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "An unexpected error occurred.");
    } finally { setLoading(false); }
  }

  async function runForecast() {
    setLoading(true); setError(""); setSuccess("");
    try {
      const data = await trainForecast(symbol.trim());
      setForecast(data);
      setSuccess(`${data.symbol} forecast trained and walk-forward evaluated.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to train forecast.");
    } finally { setLoading(false); }
  }

  return (
    <div id="top" className="app-shell">
      <Header />
      <main>
        <section className="hero">
          <div><p className="eyebrow">Market data operations console</p><h1>Reliable market data,<br /><em>ready for what comes next.</em></h1>
          <p className="subtitle">AI-Driven Forecasting &amp; Multi-Agent Platform</p></div>
          <div className="hero-note"><span>Platform status</span><strong>Data foundation + experimental ML</strong><p>Next-day forecasting is available with baseline evaluation. AI agents and automated reports remain future work.</p></div>
        </section>
        <StockSearch symbol={symbol} disabled={loading} onSymbolChange={setSymbol} onSync={() => run("sync")} onLoad={() => run("load")} />
        {loading && <LoadingState />}{error && <ErrorMessage message={error} />}
        {success && <div className="message success" role="status">{success}</div>}
        <SummaryCards result={result} symbol={symbol} />
        <ForecastPanel forecast={forecast} disabled={loading} onTrain={runForecast} />
        <section className="data-section">
          <div className="section-heading"><div><p className="eyebrow">Daily price history</p><h2>Stored market data</h2></div>{result && <span className="source-pill">{result.cached ? "Redis cache" : "SQLite"}</span>}</div>
          <StockChart rows={result?.data ?? []} symbol={result?.symbol ?? symbol.toUpperCase()} />
        </section>
      </main>
      <footer><p>For educational and research use only. This application does not provide financial advice.</p><span>Stock Agent Ops · Phase 2 experimental ML</span></footer>
    </div>
  );
}
