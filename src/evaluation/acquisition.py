"""Explicit network boundary for audit and local historical ingestion."""
from datetime import date, datetime, time, timedelta, timezone
from src.analytics.fundamentals import fundamental_history
from src.providers.vnstock import VnstockMarketDataProvider, VnstockFundamentalDataProvider, sdk, normalize_history, guarded
from src.providers.news import FixtureNewsProvider
from src.providers.base import ProviderError
from src.schemas.stocks import SymbolRequest
from .models import HistoricalObservation, DatasetManifest
from .store import digest, validate_observations

VN = timezone(timedelta(hours=7))
LIMITATIONS = [
    "Observed community SDK limit: about 8 years of daily history; requested range is not a claim of delivered coverage.",
    "Daily availability is conservatively modeled at 23:59:59 Asia/Ho_Chi_Minh; provider publication timestamps are unavailable.",
    "Downloaded history is a current vendor vintage, not an archived point-in-time vintage; later price revisions/adjustments cannot be ruled out.",
    "Price-adjustment semantics and corporate-action history are unverified; adjustment_basis=unknown.",
    "No verified exchange calendar: weekday gaps are diagnostics, not proven missing sessions.",
    "Existing normalizer collapses identical source duplicates; raw duplicate count is unavailable; conflicting duplicates fail ingestion.",
    "Fundamental disclosure timestamps and trustworthy historical sector membership are unavailable; these streams are excluded from replay.",
    "News provider is synthetic only and excluded; no live historical news coverage is claimed.",
]


def collect(symbols, start: date, end: date, benchmark="VN30"):
    if start > end or end >= datetime.now(VN).date():
        raise ValueError("Use an ordered range ending before today (completed daily sessions)")
    symbols = sorted({SymbolRequest(ticker=s).symbol for s in symbols})
    if benchmark in symbols:
        raise ValueError("Benchmark must be separate from the stock basket")
    market, financial, news = VnstockMarketDataProvider(), VnstockFundamentalDataProvider(), FixtureNewsProvider()
    observations, reports, errors = [], {}, {}
    series = {}
    quarantined = {}
    for symbol in symbols + ([benchmark] if benchmark else []):
        try:
            if symbol == benchmark:
                frame = guarded(symbol, "benchmark_history", lambda: sdk().Quote(symbol=symbol, source="VCI").history(
                    start=str(start), end=str(end), interval="1D"))
                bars = []
                quarantined[symbol] = []
                for i in range(len(frame)):
                    try:
                        bars.extend(normalize_history(frame.iloc[i:i+1], symbol, start, end))
                    except ValueError:
                        quarantined[symbol].append({"row": {k: str(v) for k,v in frame.iloc[i].to_dict().items()},
                                                    "reason": "invalid_normalized_OHLCV"})
            else:
                bars = market.get_history(symbol, start, end)
            if symbol == benchmark:
                # The stock adapter scales all prices x1000; index levels are points.
                bars = [b.model_copy(update={**{k: getattr(b, k) / 1000 for k in ("open", "high", "low", "close")},
                                             "currency": "points"}) for b in bars]
            series[symbol] = bars
            for bar in bars:
                observations.append(HistoricalObservation(ticker=symbol,
                    data_type="benchmark" if symbol == benchmark else "market",
                    observation_time=bar.date.isoformat(), available_at=datetime.combine(bar.date, time(23,59,59), VN),
                    availability_basis="end_of_day_assumption", source=bar.source, payload=bar))
        except ProviderError as exc:
            errors[symbol] = str(exc)
            series[symbol] = []
    benchmark_dates = {b.date for b in series.get(benchmark, [])}
    for symbol in symbols:
        bars = series[symbol]
        dates = {b.date for b in bars}
        weekdays = set()
        if dates:
            day = min(dates)
            while day <= max(dates):
                if day.weekday() < 5:
                    weekdays.add(day)
                day += timedelta(days=1)
        periods = []
        try:
            records = financial.get_financials(symbol)
            periods = fundamental_history(symbol, records, financial.source, limit=max(1, len(records)))
            for period in periods:
                observations.append(HistoricalObservation(ticker=symbol, data_type="fundamental",
                    observation_time=period.period, available_at=None, source=period.source, payload=period))
        except ProviderError as exc:
            errors[symbol + ":fundamentals"] = str(exc)
        articles = news.get_news(symbol)
        for item in articles:
            observations.append(HistoricalObservation(ticker=symbol, data_type="news",
                observation_time=item.published_at.isoformat(), available_at=None,
                source=item.source, is_fixture=item.is_fixture, payload=item))
        reports[symbol] = {
            "earliest_price_date": min(dates).isoformat() if dates else None,
            "latest_price_date": max(dates).isoformat() if dates else None,
            "sessions": len(bars), "normalized_duplicates": len(bars) - len(dates),
            "raw_duplicate_count": None,
            "weekday_gaps_not_verified_missing_sessions": len(weekdays - dates),
            "missing_dates_relative_to_benchmark": [d.isoformat() for d in sorted(benchmark_dates - dates)
                                                     if dates and min(dates) <= d <= max(dates)],
            "benchmark_matched_sessions": len(dates & benchmark_dates),
            "sector_metadata": "unavailable/unverified",
            "fundamental_periods": [p.period for p in periods],
            "real_fundamental_publication_timestamps": False,
            "news_count": len(articles), "news_all_fixture": all(n.is_fixture for n in articles),
            "adjustment_basis": "unknown", "source": market.source,
        }
    observations = validate_observations(observations)
    checksum = digest([r.model_dump(mode="json") for r in observations])
    now = datetime.now(timezone.utc)
    coverage = {"requested_start": str(start), "requested_end": str(end), "tickers": reports,
                "benchmark": {"symbol": benchmark, "sessions": len(benchmark_dates),
                    "earliest": str(min(benchmark_dates)) if benchmark_dates else None,
                    "latest": str(max(benchmark_dates)) if benchmark_dates else None}, "errors": errors,
                "quarantined_rows": quarantined}
    manifest = DatasetManifest(dataset_version=now.strftime("%Y%m%dT%H%M%S%fZ") + "-" + checksum[:12],
        created_at=now, source=sorted({o.source for o in observations}), tickers=symbols,
        benchmark=benchmark if benchmark_dates else None, coverage=coverage,
        known_limitations=LIMITATIONS, observation_count=len(observations), content_sha256=checksum)
    return manifest, observations
