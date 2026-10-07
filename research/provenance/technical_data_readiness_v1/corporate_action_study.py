"""Bounded, descriptive current-vintage study; not benchmark admission/calibration.

No raw SSI bars are retained. Public action notices are manually verified, not scraped.
The CLI requests only the frozen ranges below after cohort/protected identity checks.
"""
from collections import Counter
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from statistics import mean
from types import SimpleNamespace

from src.analytics.market import market_snapshot, technical_history
from src.evaluation.benchmark.exclusions import load_certified_ledger
from src.evaluation.benchmark.population import load_cohort
from src.evaluation.context import build_context
from src.materiality.detectors import detect_market_events


# Freeze before acquiring prices. Dates are ex-dates, not payment/record dates.
SAMPLE = (
    dict(symbol='VNM', ex_date='2020-09-29', record_date='2020-09-30',
         start='2020-04-01', end='2020-10-09',
         actions=['cash_dividend', 'bonus_shares'], cash_vnd=2000, new_shares_per_old=.2,
         terms_source='https://static2.vietstock.vn/vietstock/2020/8/6/20200806_20200806%20-%20VNM%20-%20CBTT%20ngay%20DKCC%20chot%20danh%20sach%20tra%20co%20tuc.pdf',
         ex_date_source='https://fica.dantri.com.vn/chung-khoan/co-dong-vinamilk-huong-loc-co-tuc-gia-co-phieu-bat-tang-manh-20200929010525937.htm'),
    dict(symbol='HDB', ex_date='2022-09-27', record_date='2022-09-28',
         start='2022-04-01', end='2022-10-07',
         actions=['stock_dividend'], cash_vnd=None, new_shares_per_old=.25,
         terms_source='https://24hmoney.vn/news/hdbank-chot-quyen-chia-co-tuc-2021-ty-le-25-c4a1629620.html',
         ex_date_source='https://24hmoney.vn/news/hdbank-chot-quyen-chia-co-tuc-2021-ty-le-25-c4a1629620.html'),
    dict(symbol='GAS', ex_date='2023-09-22', record_date='2023-09-25',
         start='2023-04-01', end='2023-10-06',
         actions=['bonus_shares'], cash_vnd=None, new_shares_per_old=.2,
         terms_source='https://www.vsd.vn/vi/ad/161638',
         ex_date_source='https://archive.shs.com.vn/Sites/QuoteVN/SiteRoot/reportattach/20230912_172533_Market%20Lens%20Final%20New%2012-09-2023.pdf'),
    dict(symbol='GAS', ex_date='2024-09-13', record_date='2024-09-16',
         start='2024-04-01', end='2024-09-27',
         actions=['cash_dividend', 'bonus_shares'], cash_vnd=6000, new_shares_per_old=.02,
         terms_source='https://web.vsd.vn/vi/ad/174104',
         ex_date_source='https://cophieu68.vn/quote/history.php?cP=6&id=gas'),
)
KINDS = ('abnormal_price_move', 'unusual_volume', 'ma_cross', 'rsi_regime_entry',
         'bollinger_lower_reversal_volume', 'bollinger_upper_reversal_volume')


def validate_scope(sample, cohort, ledger):
    """Conservative research restriction, not a change to benchmark eligibility.

Episode bounds are unresolved: use only issuers absent from all protected records.
This deliberately quarantines the SSI rights example; never inspect protected prices.
"""
    protected = {r['ticker'] for s in ledger['studies'] for r in s['records']}
    for item in sample:
        start, ex, end = (date.fromisoformat(item[k]) for k in ('start', 'ex_date', 'end'))
        if item['symbol'] not in cohort or item['symbol'] in protected:
            raise ValueError('Cohort/protected scope violation')
        if not date(2020, 1, 1) <= start <= ex <= end < date(2025, 1, 1):
            raise ValueError('Date scope violation')


def session_distance(sessions, event_date, action_date):
    """Observed trading-row distance; no weekend/holiday inference or date snapping."""
    if event_date not in sessions or action_date not in sessions:
        return None
    return sessions.index(event_date) - sessions.index(action_date)


def overlap_counts(events, sessions, action_date):
    if action_date not in sessions:
        raise ValueError('Missing action/event session')
    result = {}
    for width in range(4):
        inside = Counter()
        outside = Counter()
        for day, kind in events:
            distance = session_distance(sessions, day, action_date)
            if distance is None:
                raise ValueError('Missing action/event session')
            (inside if abs(distance) <= width else outside)[kind] += 1
        result[str(width)] = {'inside': {k: inside[k] for k in KINDS},
                              'outside': {k: outside[k] for k in KINDS}}
    return result


def analyze(item, bars):
    if not bars or any(b.ticker != item['symbol'] for b in bars):
        raise ValueError('Missing/mismatched series')
    if any(not date.fromisoformat(item['start']) <= b.date <= date.fromisoformat(item['end']) for b in bars):
        raise ValueError('Provider returned out-of-scope row')
    sessions = [b.date for b in bars]
    if sessions != sorted(set(sessions)):
        raise ValueError('Unordered/duplicate sessions')
    action = date.fromisoformat(item['ex_date'])
    if action not in sessions:
        raise ValueError('Ex-date absent; do not infer from record date')
    t = sessions.index(action)
    if t < 65 or t + 5 >= len(bars):
        raise ValueError('Insufficient warmup or event window')
    technical = technical_history(item['symbol'], bars, bars[0].source)
    config = SimpleNamespace(lookback_sessions=252, min_history=60)
    past, candidates, tail_candidates, diagnostics = [], [], [], []
    for i, bar in enumerate(bars):
        snapshot = market_snapshot(bar.ticker, bars[:i+1], bar.source)
        raw, contexts = build_context(snapshot, technical[i], past, bar.volume, None, config)
        events = detect_market_events(technical[i-1] if i else None, technical[i], contexts,
            recent_bars=technical[max(0, i-2):i+1], relative_volume=raw['relative_volume'])
        if abs(i-t) <= 5:
            for event in events:
                kind = event.event_type.value
                candidates.append((bar.date, kind))
                # Descriptive q95 MIDRANK subset; not D1 nearest-rank factual labels.
                if kind not in ('abnormal_price_move', 'unusual_volume') or event.own_history_abnormality >= .95:
                    tail_candidates.append((bar.date, kind))
            diagnostics.append(dict(distance=i-t, return_1d=snapshot.daily_return,
                return_5d=snapshot.return_5d, return_20d=snapshot.return_20d,
                range_fraction=(bar.high-bar.low)/bars[i-1].close,
                ma_spread=raw['ma_spread'], rsi14=technical[i].rsi14,
                bb_width_fraction=(technical[i].bb50_upper-technical[i].bb50_lower)/technical[i].ma50,
                volatility_20d=snapshot.volatility_20d, relative_volume_prior=raw['relative_volume'],
                volume_rank=contexts['unusual_volume'].own_history_abnormality))
        past.append(raw)
    normalized = json.dumps([b.model_dump(mode='json') for b in bars], sort_keys=True, separators=(',', ':'))
    prior_volume = mean(b.volume for b in bars[t-5:t])
    return dict(sample=item, rows=len(bars), first=str(sessions[0]), last=str(sessions[-1]),
        normalized_sha256=sha256(normalized.encode()).hexdigest(), diagnostics=diagnostics,
        post_pre_5_session_mean_volume_ratio=mean(b.volume for b in bars[t+1:t+6])/prior_volume if prior_volume > 0 else None,
        candidate_overlap=overlap_counts(candidates, sessions, action),
        q95_subset_overlap=overlap_counts(tail_candidates, sessions, action))


def main():
    from src.providers.ssi import SsiMarketDataProvider
    from src.providers.base import ProviderError
    validate_scope(SAMPLE, load_cohort().tickers, load_certified_ledger())
    results = []
    with SsiMarketDataProvider() as provider:
        for item in SAMPLE:
            try:
                bars = provider.get_history(item['symbol'], date.fromisoformat(item['start']), date.fromisoformat(item['end']))
                results.append(analyze(item, bars))
            except ProviderError:
                results.append(dict(sample=item, status='PROVIDER_REJECTED', diagnostics=None))
    print(json.dumps(dict(acquired_at=datetime.now(timezone.utc).isoformat(),
        scope='DESCRIPTIVE_CURRENT_VINTAGE_NOT_PIT_NOT_CALIBRATION', results=results), indent=2))


if __name__ == '__main__':
    main()
