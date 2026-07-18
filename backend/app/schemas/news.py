from datetime import datetime

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str
    banner_image: str | None = None
    sentiment_label: str
    sentiment_score: float = Field(ge=-1, le=1)
    relevance_score: float = Field(ge=0, le=1)


class StockNewsResponse(BaseModel):
    symbol: str
    count: int
    cached: bool
    data: list[NewsArticle]
