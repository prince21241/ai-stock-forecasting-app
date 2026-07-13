interface StockSearchProps {
  symbol: string;
  disabled: boolean;
  onSymbolChange: (symbol: string) => void;
  onSync: () => void;
  onLoad: () => void;
}

export function StockSearch({ symbol, disabled, onSymbolChange, onSync, onLoad }: StockSearchProps) {
  return (
    <form className="search-panel" onSubmit={(event) => { event.preventDefault(); onSync(); }}>
      <label htmlFor="symbol">Stock symbol</label>
      <div className="search-controls">
        <input
          id="symbol"
          value={symbol}
          onChange={(event) => onSymbolChange(event.target.value.toUpperCase())}
          placeholder="AAPL"
          maxLength={15}
          autoComplete="off"
          spellCheck={false}
          aria-describedby="symbol-help"
        />
        <button className="button primary" type="submit" disabled={disabled || !symbol.trim()}>
          Synchronize Data
        </button>
        <button className="button secondary" type="button" onClick={onLoad} disabled={disabled || !symbol.trim()}>
          Load Stored Data
        </button>
      </div>
      <p id="symbol-help">Use a market ticker such as AAPL, MSFT, BRK.B, or RDS-A.</p>
    </form>
  );
}

