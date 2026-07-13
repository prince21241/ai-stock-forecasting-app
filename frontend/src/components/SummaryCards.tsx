import type { StockListResponse } from "../types/stock";

interface SummaryCardsProps { result: StockListResponse | null; symbol: string; }

const priceFormatter = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });

export function SummaryCards({ result, symbol }: SummaryCardsProps) {
  const latest = result?.data[0];
  const cards = [
    ["Current symbol", result?.symbol ?? (symbol.toUpperCase() || "—")],
    ["Latest close", latest ? priceFormatter.format(Number(latest.close_price)) : "—"],
    ["Latest trading date", latest?.trading_date ?? "—"],
    ["Returned records", result ? result.count.toLocaleString() : "0"],
  ];
  return (
    <section className="summary-grid" aria-label="Stock summary">
      {cards.map(([label, value]) => (
        <article className="summary-card" key={label}>
          <span>{label}</span><strong>{value}</strong>
        </article>
      ))}
    </section>
  );
}
