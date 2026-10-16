"""October 16 cache hypotheses, using fake time/transport, never live SSI."""
from datetime import datetime
from types import SimpleNamespace

from src.providers.ssi.live import LEASE, SsiLiveMarket, VN, normalize_trade


class OneTick:
    def __init__(self): self.calls = 0
    def wait(self, seconds):
        assert seconds == 1
        self.calls += 1
        return self.calls > 1


class Stream:
    is_connected = True
    def __init__(self): self.sent = []; self.disconnected = False
    def send(self, row): self.sent.append(row)
    def disconnect(self): self.disconnected = True


def fixture():
    state = {'elapsed': 0, 'now': datetime(2026, 10, 16, 14, 36, tzinfo=VN)}
    calls = []
    def request(endpoint, params):
        calls.append((endpoint, params))
        return {'data': []}  # Explicit missing provider result, not a fabricated quote.
    provider = SimpleNamespace(_request=request, _auth=SimpleNamespace(is_token_expired=False))
    market = SsiLiveMarket(provider, clock=lambda: state['now'], monotonic=lambda: state['elapsed'])
    market.reference_day = state['now'].date()
    market.thread = object()  # Suppress background work; run exactly one maintenance iteration.
    market.ws = Stream()
    return market, state, calls


def cached(market, symbol):
    market.cache[symbol] = normalize_trade(
        {'s': symbol, 't': '2026/10/16 13:13:42', 'p': 10000}, 9900, market.clock())


def tick(market):
    market.stop = OneTick()
    market._maintain()


def test_expired_lease_disconnects_without_erasing_or_relabeling_cached_price():
    market, state, calls = fixture()
    cached(market, 'PNJ')
    assert market.read(['PNJ'], 'visible')['items']['PNJ']['status'] == 'stale'
    stream = market.ws
    state['elapsed'] = LEASE + 1
    tick(market)
    assert stream.disconnected and not market.subscribed and not market.demand
    assert market.cache['PNJ']['updated_at'] == '2026-10-16T13:13:42+07:00'
    assert calls == []


def test_new_subscription_does_not_invent_missing_quote_from_reference_metadata():
    market, state, calls = fixture()
    market.references['VCB'] = (state['now'].date(), 60000)
    first = market.read(['VCB'], 'monitor')
    assert first['items']['VCB'] == {'status': 'unavailable', 'snapshot': None}
    assert calls == []  # Response precedes asynchronous subscription/bootstrap.
    tick(market)
    assert market.subscribed == {'VCB'}
    assert len(calls) == 1 and calls[0][1]['symbol'] == 'VCB'
    assert market.read(['VCB'], 'monitor')['items']['VCB']['snapshot'] is None


def test_renewed_active_lease_keeps_old_cache_stale_until_a_source_event():
    market, state, calls = fixture()
    cached(market, 'HPG')
    old = market.read(['HPG'], 'visible')['items']['HPG']
    tick(market)
    assert market.subscribed == {'HPG'} and calls == []
    assert old['status'] == 'stale'
    assert market.read(['HPG'], 'visible')['items']['HPG']['snapshot']['updated_at'] == old['snapshot']['updated_at']
    market.accept({'topic': 'trade.HPG', 'data': {
        's': 'HPG', 't': '2026/10/16 14:35:58', 'p': 10100}})
    fresh = market.read(['HPG'], 'visible')['items']['HPG']
    assert fresh['status'] == 'fresh'
    assert fresh['snapshot']['updated_at'] == '2026-10-16T14:35:58+07:00'
    assert fresh['snapshot']['updated_at'] != state['now'].isoformat()


def test_release_removes_only_its_client_and_ignores_late_unrequested_ticks():
    market, state, calls = fixture()
    market.read(['PNJ', 'VCB'], 'one')
    market.read(['HPG'], 'two')
    market.release('one')
    assert set(market.demand) == {'HPG'}
    market.accept({'topic': 'trade.PNJ', 'data': {
        's': 'PNJ', 't': '2026/10/16 14:35:58', 'p': 10100}})
    assert 'PNJ' not in market.cache and calls == []
