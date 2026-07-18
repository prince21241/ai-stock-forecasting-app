import type { NewsArticle } from "../types/stock";

function sentimentClass(label: string) {
  const value = label.toLowerCase();
  if (value.includes("bullish")) return "bullish";
  if (value.includes("bearish")) return "bearish";
  return "neutral";
}

export function StockNews({ symbol, articles, loading, error, cached }: {
  symbol: string; articles: NewsArticle[]; loading: boolean; error: string; cached: boolean;
}) {
  return <section className="news-section">
    <div className="section-heading"><div><p className="eyebrow">Market intelligence</p><h2>Latest {symbol} news</h2></div>
      {articles.length > 0 && <span className="source-pill">{cached ? "Cached" : "Alpha Vantage"}</span>}</div>
    {loading && <div className="news-empty">Loading the latest headlines…</div>}
    {!loading && error && <div className="message error"><span><strong>News unavailable</strong> {error}</span></div>}
    {!loading && !error && articles.length === 0 && <div className="news-empty">Load a stock to see its latest news.</div>}
    {!loading && articles.length > 0 && <div className="news-grid">{articles.map((article) =>
      <article className="news-card" key={article.url}>
        {article.banner_image && <img src={article.banner_image} alt="" loading="lazy" />}
        <div className="news-card-body"><div className="news-meta"><span>{article.source}</span><time dateTime={article.published_at}>{new Date(article.published_at).toLocaleString()}</time></div>
          <h3><a href={article.url} target="_blank" rel="noreferrer">{article.title}</a></h3>
          <p>{article.summary}</p>
          <div className="news-footer"><span className={`sentiment ${sentimentClass(article.sentiment_label)}`}>{article.sentiment_label}</span><span>{Math.round(article.relevance_score * 100)}% ticker relevance</span></div>
        </div>
      </article>)}</div>}
  </section>;
}
