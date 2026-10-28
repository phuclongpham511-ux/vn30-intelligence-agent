"""Explicit demonstration data; never presented as live reporting."""
from datetime import datetime, timezone
from src.schemas.data import NewsItem


class FixtureNewsProvider:
    source = "local-fixture"

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        return [NewsItem(
            id=f"fixture-{symbol}-section1", ticker=symbol,
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            title=f"[Sample] {symbol} news feed demonstration",
            summary_or_content="Synthetic interface example only. This is not an actual company announcement.",
            source=self.source, url=None, is_fixture=True,
        )][:limit]
