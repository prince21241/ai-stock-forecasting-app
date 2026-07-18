import { useEffect, useMemo, useRef, useState } from "react";
import {
  ColorType,
  CandlestickSeries,
  createChart,
  CrosshairMode,
  HistogramSeries,
  type BusinessDay,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import type { StockPrice } from "../types/stock";

type Range = "1M" | "3M" | "6M" | "1Y" | "ALL";

const ranges: Range[] = ["1M", "3M", "6M", "1Y", "ALL"];
const price = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const volume = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

function toBusinessDay(date: string): BusinessDay {
  const [year, month, day] = date.split("-").map(Number);
  return { year, month, day };
}

export function chartData(rows: StockPrice[]) {
  const ascending = [...rows].sort((a, b) => a.trading_date.localeCompare(b.trading_date));
  return {
    candles: ascending.map<CandlestickData<Time>>((row) => ({
      time: toBusinessDay(row.trading_date),
      open: Number(row.open_price),
      high: Number(row.high_price),
      low: Number(row.low_price),
      close: Number(row.close_price),
    })),
    volumes: ascending.map<HistogramData<Time>>((row) => ({
      time: toBusinessDay(row.trading_date),
      value: row.volume,
      color: Number(row.close_price) >= Number(row.open_price) ? "rgba(40, 136, 91, .55)" : "rgba(198, 66, 55, .55)",
    })),
    ascending,
  };
}

function rangeStart(lastDate: string, range: Range): string | null {
  if (range === "ALL") return null;
  const date = new Date(`${lastDate}T00:00:00Z`);
  const months = { "1M": 1, "3M": 3, "6M": 6, "1Y": 12 }[range];
  date.setUTCMonth(date.getUTCMonth() - months);
  return date.toISOString().slice(0, 10);
}

interface StockChartProps { rows: StockPrice[]; symbol: string; }

export function StockChart({ rows, symbol }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [range, setRange] = useState<Range>("6M");
  const [hovered, setHovered] = useState<StockPrice | null>(null);
  const data = useMemo(() => chartData(rows), [rows]);

  useEffect(() => {
    if (!containerRef.current || !data.candles.length) return;
    const container = containerRef.current;
    const chart = createChart(container, {
      width: container.clientWidth,
      height: 510,
      layout: { background: { type: ColorType.Solid, color: "#faf9f5" }, textColor: "#68736c", fontFamily: "DM Sans, sans-serif" },
      grid: { vertLines: { color: "#e8e8e0" }, horzLines: { color: "#e1e1d9" } },
      crosshair: { mode: CrosshairMode.Normal, vertLine: { color: "#748178", labelBackgroundColor: "#173f2f" }, horzLine: { color: "#748178", labelBackgroundColor: "#173f2f" } },
      rightPriceScale: { borderColor: "#d7d7ce", scaleMargins: { top: 0.08, bottom: 0.24 } },
      timeScale: { borderColor: "#d7d7ce", timeVisible: false, rightOffset: 2, barSpacing: 8, minBarSpacing: 3 },
      handleScroll: true,
      handleScale: true,
    });
    chartRef.current = chart;
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#28885b", downColor: "#c64237", borderUpColor: "#28885b", borderDownColor: "#c64237", wickUpColor: "#28885b", wickDownColor: "#c64237",
      priceLineVisible: true,
    });
    candles.setData(data.candles);
    const volumes = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceScaleId: "volume", lastValueVisible: false, priceLineVisible: false });
    volumes.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volumes.setData(data.volumes);
    chart.subscribeCrosshairMove((param) => {
      if (!param.time) { setHovered(null); return; }
      const time = param.time as BusinessDay;
      const date = `${time.year}-${String(time.month).padStart(2, "0")}-${String(time.day).padStart(2, "0")}`;
      setHovered(data.ascending.find((row) => row.trading_date === date) ?? null);
    });
    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width }));
    observer.observe(container);
    return () => { observer.disconnect(); chart.remove(); chartRef.current = null; };
  }, [data]);

  useEffect(() => {
    const chart = chartRef.current;
    const last = data.ascending.at(-1)?.trading_date;
    if (!chart || !last) return;
    const start = rangeStart(last, range);
    if (!start) chart.timeScale().fitContent();
    else chart.timeScale().setVisibleRange({ from: start as Time, to: last as Time });
  }, [data, range]);

  if (!rows.length) {
    return <div className="empty-state"><strong>No stored data loaded</strong><span>Synchronize a symbol or load existing SQLite records.</span></div>;
  }

  const detail = hovered ?? data.ascending.at(-1)!;
  const rose = Number(detail.close_price) < Number(detail.open_price);
  return (
    <div className="chart-card">
      <div className="chart-toolbar">
        <div className="chart-quote">
          <span className="symbol-swatch" aria-hidden="true" />
          <div><strong>{symbol}</strong><span>{detail.trading_date}</span></div>
          <div className={`quote-value ${rose ? "down" : "up"}`}><strong>{price.format(Number(detail.close_price))}</strong><span>O {price.format(Number(detail.open_price))} · H {price.format(Number(detail.high_price))} · L {price.format(Number(detail.low_price))} · Vol {volume.format(detail.volume)}</span></div>
        </div>
        <div className="range-control" aria-label="Chart date range">
          {ranges.map((item) => <button key={item} type="button" className={range === item ? "active" : ""} aria-pressed={range === item} onClick={() => setRange(item)}>{item}</button>)}
        </div>
      </div>
      <div ref={containerRef} className="stock-chart" role="img" aria-label={`${symbol} candlestick price chart with daily volume`} />
      <p className="chart-help">Scroll to move through time · Pinch or scroll over the chart to zoom · Hover for daily OHLCV values</p>
    </div>
  );
}
