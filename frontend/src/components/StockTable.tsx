import type { StockPrice } from "../types/stock";

const price = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
const volume = new Intl.NumberFormat("en-US");

export function StockTable({ rows }: { rows: StockPrice[] }) {
  if (!rows.length) {
    return <div className="empty-state"><strong>No stored data loaded</strong><span>Synchronize a symbol or load existing SQLite records.</span></div>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.trading_date}>
              <td>{row.trading_date}</td><td>{price.format(Number(row.open_price))}</td>
              <td>{price.format(Number(row.high_price))}</td><td>{price.format(Number(row.low_price))}</td>
              <td className="close-value">{price.format(Number(row.close_price))}</td><td>{volume.format(row.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
