"""Demand-leased SSI presentation data. Never an input to daily analytics."""
from datetime import datetime, timedelta
import math
import re
from threading import Event, RLock, Thread
import time
from zoneinfo import ZoneInfo

from ssi_sdk.constant import EP_DATA_MASTER_DATA, EP_DATA_OHLC, EP_DATA_INDEX_SUMMARY
from ssi_sdk.transport.websocket_client import WebSocketClient

VN = ZoneInfo('Asia/Ho_Chi_Minh')
MAX_SYMBOLS = 50
MAX_CACHE = 256
TTL = 10
LEASE = 75


def vietnam_now():
    return datetime.now(VN)


def normalize_symbols(raw):
    values = raw.split(',') if isinstance(raw, str) else raw
    if len(values) > MAX_SYMBOLS:
        raise ValueError('Request at most 50 symbols')
    symbols = []
    for value in values:
        value = value.strip().upper()
        if not re.fullmatch(r'[A-Z0-9]{1,20}', value):
            raise ValueError('Invalid ticker')
        if value not in symbols:
            symbols.append(value)
    return symbols


def number(row, key, *, positive=False, nonnegative=False):
    value = row.get(key)
    if value is None or value == '':
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Invalid number')
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise ValueError('Invalid number')
    return value


def timestamp(value, now):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,6})?', value):
        raise ValueError('Invalid source timestamp')
    parsed = datetime.fromisoformat(value.replace('/', '-')).replace(tzinfo=VN)
    if parsed > now + timedelta(seconds=5):
        raise ValueError('Future source timestamp')
    return parsed


def session_state(now, *, confirmed_day=None):
    now = now.astimezone(VN)
    minute = now.hour * 60 + now.minute
    if now.weekday() >= 5 or minute < 9 * 60 or minute >= 15 * 60:
        return 'closed'
    if 11 * 60 + 30 <= minute < 13 * 60:
        return 'break'
    # Fresh, dated source data confirms today's trading; no invented holiday calendar.
    return 'active' if confirmed_day == now.date() else 'unknown'


def source_fresh(updated, now, state, max_age=120):
    if updated.date() != now.date():
        return False
    if (now-updated).total_seconds() <= max_age:
        return True
    minute = updated.hour*60+updated.minute
    return (state == 'break' and minute >= 11*60+28) or (state == 'closed' and now.hour >= 15 and minute >= 14*60+45)


def normalize_trade(row, reference, now):
    ticker = normalize_symbols([row['s']])[0]
    updated = timestamp(row['t'], now)
    price = number(row, 'p', positive=True)
    if price is None:
        raise ValueError('Missing price')
    if reference is not None and (not math.isfinite(reference) or reference <= 0):
        raise ValueError('Invalid reference')
    change = price - reference if reference is not None else None
    return dict(ticker=ticker, last_price=price, reference_price=reference, change=change,
                change_percent=change / reference * 100 if change is not None else None,
                open=number(row, 'o', positive=True), high=number(row, 'h', positive=True),
                low=number(row, 'l', positive=True), total_volume=number(row, 'v', nonnegative=True),
                total_value=None, trading_date=updated.date().isoformat(), updated_at=updated.isoformat(),
                source='SSI:FastConnect:trade', price_unit='VND', session='unknown')


class SsiLiveMarket:
    """One process stream, only requested equity topics, expiring demand and bounded cache.

    REST reference metadata is acquired once per Vietnam day, not live-universe polling.
    SDK raw transport preserves missing fields and keeps authentication server-side.
    """
    def __init__(self, provider, *, clock=vietnam_now, monotonic=time.monotonic, websocket=WebSocketClient):
        self.provider = provider
        self.clock, self.monotonic, self.websocket = clock, monotonic, websocket
        self.lock = RLock()
        self.io = RLock()
        self.stop = Event()
        self.ws = None
        self.thread = None
        self.demand = {}
        self.leases = {}
        self.subscribed = set()
        self.cache = {}
        self.references = {}
        self.reference_day = None
        self.retry_at = 0
        self.index_cache = None
        self.index_at = -float('inf')
        self.index_failed = False
        self.index_retry_at = 0
        self.closed_attempts = {}

    def _bootstrap(self, symbol, now):
        cached = self.cache.get(symbol)
        if cached and (session_state(now) not in ('closed','break') or source_fresh(datetime.fromisoformat(cached['updated_at']),now,session_state(now))):
            return
        if self.monotonic() - self.closed_attempts.get(symbol, -float('inf')) < 60:
            return
        self.closed_attempts[symbol] = self.monotonic()
        while len(self.closed_attempts) > MAX_CACHE:
            self.closed_attempts.pop(next(iter(self.closed_attempts)))
        try:
            rows = self.provider._request(EP_DATA_OHLC, {'symbol':symbol,
                'from':(now.date()-timedelta(days=7)).strftime('%Y/%m/%d 00:00:00'),
                'to':now.strftime('%Y/%m/%d %H:%M:%S'), 'timeFrame':'1m',
                'pageIndex':1, 'pageSize':2}).get('data', [])
            row = max(rows, key=lambda r: timestamp(r['tradingDate'], now))
            if row.get('symbol') != symbol:
                raise ValueError('Mismatched source ticker')
            ref = self.references.get(symbol)
            day = timestamp(row['tradingDate'], now).date()
            snapshot = normalize_trade({'s':symbol, 't':row['tradingDate'], 'p':row.get('close')},
                                      ref[1] if ref and ref[0] == day else None, now)
            snapshot['source'] = 'SSI:FastConnect:ohlc:1m'
            with self.lock:
                previous = self.cache.get(symbol)
                if previous is None or previous['updated_at'] < snapshot['updated_at']:
                    self.cache[symbol] = snapshot
                while len(self.cache) > MAX_CACHE:
                    self.cache.pop(next(iter(self.cache)))
        except Exception as exc:
            self.closed_attempts[symbol] = self.monotonic()+max(0,(getattr(exc,'retry_after',None) or 60)-60)

    def close(self):
        self.stop.set()
        with self.io:
            if self.ws:
                self.ws.disconnect()
                self.ws = None
        if self.thread:
            self.thread.join(timeout=3)

    def _references(self):
        day = self.clock().astimezone(VN).date()
        if self.reference_day == day:
            return
        records = {}
        text = day.strftime('%Y/%m/%d')
        for page in range(1, 5):
            payload = self.provider._request(EP_DATA_MASTER_DATA, {'from': text, 'to': text,
                                             'pageIndex': page, 'pageSize': 1000})
            if isinstance(payload,dict) and payload.get('code') == 204 and session_state(self.clock()) == 'closed':
                payload = self.provider._request(EP_DATA_MASTER_DATA, {'pageIndex':page,'pageSize':1000})
            if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
                raise ValueError('Reference metadata unavailable')
            pages = int(payload.get('pagesCount', 1))
            if pages > 4:
                raise ValueError('Reference metadata exceeds bound')
            for row in payload['data']:
                try:
                    date = datetime.strptime(row['tradingDate'], '%Y/%m/%d').date()
                    reference = number(row, 'refPrice', positive=True)
                    if date <= day and reference is not None:
                        records[row['symbol']] = (date, reference)
                except (KeyError, TypeError, ValueError):
                    continue
            if page >= pages:
                break
        self.references, self.reference_day = records, day

    def accept(self, message):
        """Raw SSI DATA boundary. Unrequested and invalid messages are discarded."""
        row = message.get('data')
        if not isinstance(row, dict) or message.get('topic') != 'trade.' + str(row.get('s')):
            return
        now = self.clock().astimezone(VN)
        with self.lock:
            symbol = row.get('s')
            if self.demand.get(symbol, 0) <= self.monotonic():
                return
            try:
                ref = self.references.get(symbol)
                day = timestamp(row['t'], now).date()
                snapshot = normalize_trade(row, ref[1] if ref and ref[0] == day else None, now)
                previous = self.cache.get(symbol)
                if previous and previous['updated_at'] > snapshot['updated_at']:
                    return
                self.cache[symbol] = snapshot
                while len(self.cache) > MAX_CACHE:
                    self.cache.pop(next(iter(self.cache)))
            except (ValueError, TypeError, KeyError):
                return

    def _maintain(self):
        while not self.stop.wait(1):
            try:
                with self.io:
                    now = self.clock().astimezone(VN)
                    with self.lock:
                        requested = {s for s, expiry in self.demand.items() if expiry > self.monotonic()}
                        self.demand = {s: self.demand[s] for s in requested}
                    if session_state(now) in ('closed', 'break') or not requested:
                        if self.ws:
                            self.ws.disconnect()
                            self.ws = None
                        self.subscribed.clear()
                        continue
                    if self.monotonic() < self.retry_at:
                        continue
                    self._references()
                    if self.ws is None or not self.ws.is_connected:
                        if self.ws:
                            self.ws.disconnect()
                        self.ws = self.websocket(self.provider._auth.config)
                        self.ws.set_token(self.provider._auth.token_manager.access_token)
                        self.ws.on('DATA', self.accept)
                        self.ws.connect()
                        self.subscribed.clear()
                    # Proactively refresh through the existing authenticated transport.
                    if self.provider._auth.is_token_expired:
                        self.reference_day = None
                        self._references()
                        self.ws.set_token(self.provider._auth.token_manager.access_token)
                        self.ws.disconnect()
                        self.ws.connect()
                        self.subscribed.clear()
                    for method, symbols in [('unsubscribe', self.subscribed - requested),
                                            ('subscribe', requested - self.subscribed)]:
                        if symbols:
                            self.ws.send({'method': method, 'channel': 'DATA',
                                          'topics': ['trade.' + s for s in sorted(symbols)]})
                    self.subscribed = requested
                    # Quiet equities need an initial level; never repeat this for cached symbols.
                    for symbol in sorted(requested - set(self.cache))[:2]:
                        self._bootstrap(symbol, now)
            except Exception as exc:
                # No upstream exception text, payloads, headers or tokens reach logs/API.
                self.retry_at = self.monotonic() + max(30, getattr(exc,'retry_after',None) or 0)
                if self.ws:
                    self.ws.disconnect()
                    self.ws = None
                self.subscribed.clear()

    def release(self, client_id):
        with self.lock:
            self.leases.pop(client_id, None)
            self._demands()

    def _demands(self):
        self.leases = {key: value for key, value in self.leases.items() if value[1] > self.monotonic()}
        self.demand = {}
        for symbols, expiry in self.leases.values():
            for symbol in symbols:
                self.demand[symbol] = max(expiry, self.demand.get(symbol, 0))

    def read(self, symbols, client_id='default'):
        symbols = normalize_symbols(symbols)
        now = self.clock().astimezone(VN)
        if session_state(now) in ('closed', 'break'):
            # One bounded latest-price acquisition on revisit, not a closed-market loop.
            with self.io:
                try:
                    self._references()
                except Exception:
                    pass
                for symbol in symbols:
                    self._bootstrap(symbol, now)
        with self.lock:
            self._demands()
            if len(set(self.demand) | set(symbols)) > MAX_CACHE:
                return {'items': {s: {'status': 'unavailable', 'snapshot': None} for s in symbols},
                        'session': 'unknown', 'as_of': now.isoformat()}
            if client_id not in self.leases and len(self.leases) >= MAX_CACHE:
                return {'items': {s: {'status': 'unavailable', 'snapshot': None} for s in symbols},
                        'session': 'unknown', 'as_of': now.isoformat()}
            self.leases[client_id] = (symbols, self.monotonic()+LEASE)
            self._demands()
            if symbols and self.thread is None:
                self.thread = Thread(target=self._maintain, name='ssi-live-demand', daemon=True)
                self.thread.start()
            evidence = [datetime.fromisoformat(r['updated_at']) for r in self.cache.values()]
            confirmed = now.date() if any(r.date() == now.date() and 0 <= (now-r).total_seconds() <= 180 for r in evidence) else None
            state = session_state(now, confirmed_day=confirmed)
            items = {}
            for s in symbols:
                row = self.cache.get(s)
                if row:
                    row = dict(row, session=state)
                    fresh = source_fresh(datetime.fromisoformat(row['updated_at']),now,state)
                    items[s] = {'status': 'fresh' if fresh else 'stale', 'snapshot': row}
                else:
                    items[s] = {'status': 'unavailable', 'snapshot': None}
            return {'items': items, 'session': state, 'as_of': now.isoformat()}

    def index(self):
        """Current-minute index presentation; previous summary is never dated as today."""
        with self.io:
            now = self.clock().astimezone(VN)
            if self.monotonic() - self.index_at >= TTL and self.monotonic() >= self.index_retry_at:
                self.index_at = self.monotonic()
                try:
                    start = (now.date() - timedelta(days=7)).strftime('%Y/%m/%d 00:00:00')
                    end = now.strftime('%Y/%m/%d %H:%M:%S')
                    result = self.provider._request(EP_DATA_OHLC, {'symbol':'VNINDEX', 'from':start,
                                      'to':end, 'timeFrame':'1m', 'pageIndex':1, 'pageSize':2})
                    rows = result.get('data', []) if isinstance(result, dict) else []
                    if not rows:
                        raise ValueError('Index unavailable')
                    row = max(rows, key=lambda r: timestamp(r['tradingDate'], now))
                    if row.get('symbol') != 'VNINDEX':
                        raise ValueError('Mismatched index identity')
                    updated = timestamp(row['tradingDate'], now)
                    level = number(row, 'close', positive=True)
                    if level is None:
                        raise ValueError('Index unavailable')
                    # IndexSummary's previous completed close is the authoritative baseline.
                    # Verify the previous completed session; do not label a multi-day
                    # summary gap as intraday movement. This does not change daily admission.
                    reference = None
                    try:
                        summary = self.provider.get_index_snapshot()
                        history = self.provider.get_history('VNINDEX', updated.date()-timedelta(days=14), updated.date()-timedelta(days=1))
                        prior_day = history[-1].date.isoformat() if history else None
                        if summary['trading_date'] == updated.date().isoformat() and summary['change'] is not None:
                            reference = summary['level']-summary['change']
                        elif summary['trading_date'] == prior_day:
                            reference = summary['level']
                        if reference is not None and (not math.isfinite(reference) or reference <= 0):
                            reference = None
                    except Exception:
                        # A missing reference cannot erase a legitimate current level.
                        pass
                    change = level-reference if reference else None
                    self.index_cache = dict(index='VNINDEX', level=level, change=change,
                        change_percent=change/reference*100 if change is not None else None,
                        total_volume=None, total_value=None, trading_date=updated.date().isoformat(),
                        updated_at=updated.isoformat(), fetched_at=now.isoformat(),
                        source='SSI:FastConnect:ohlc:1m', timestamp_precision='minute')
                    self.index_failed = False
                except Exception as exc:
                    self.index_failed = True
                    self.index_retry_at = self.monotonic()+max(TTL,getattr(exc,'retry_after',None) or 0)
            if not self.index_cache:
                return {'snapshot': None, 'status':'unavailable', 'session':session_state(now), 'as_of':now.isoformat()}
            row = dict(self.index_cache)
            updated = datetime.fromisoformat(row['updated_at'])
            age = (now-updated).total_seconds()
            confirmed = now.date() if updated.date() == now.date() and age <= 180 else None
            state = session_state(now, confirmed_day=confirmed)
            fresh = not self.index_failed and source_fresh(updated,now,state,180)
            return {'snapshot':dict(row,session=state), 'status':'fresh' if fresh else 'stale',
                    'session':state, 'as_of':now.isoformat()}
