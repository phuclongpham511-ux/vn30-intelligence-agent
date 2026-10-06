"""SSI 3.2.1 authenticated raw transport; SDK models must not fabricate zeros."""
from datetime import date, datetime, timedelta
from functools import lru_cache
import logging
import math
import re
from threading import RLock
import time
from zoneinfo import ZoneInfo

from ssi_sdk import Auth, Config
from ssi_sdk.constant import EP_DATA_OHLC, EP_DATA_SECURITIES_BY_BOARD

from src.config.settings import get_settings
from src.providers.base import ProviderError, ProviderNotReadyError
from src.schemas.data import MarketBar

logger = logging.getLogger(__name__)
PAGE_SIZE = 100
MAX_PAGES = 16


def vietnam_today() -> date:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def daily_bounds(start: date, end: date) -> tuple[str, str]:
    return start.strftime("%Y/%m/%d 00:00:00"), end.strftime("%Y/%m/%d 23:59:59")


def numeric(row: dict, key: str) -> float:
    raw = row.get(key)
    if raw is None or isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
        raise ValueError("Missing or invalid numeric field")
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError("Non-finite numeric field")
    return value


class SsiMarketDataProvider:
    source = "SSI:FastConnect"

    def __init__(self, settings=None, *, transport=None, today=None):
        self._settings = settings if settings is not None else get_settings()
        self._transport = transport
        self._today = today if today is not None else vietnam_today
        self._auth = None
        self._lock = RLock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        with self._lock:
            if self._auth is not None:
                self._auth.close()
                self._auth = None

    def _ready(self):
        if not self._settings.ssi_api_key.get_secret_value() or not self._settings.ssi_api_secret.get_secret_value():
            raise ProviderNotReadyError("SSI Market Data credentials are not configured.")

    def _request(self, path, params):
        # Serialize shared token/transport use. Refresh is proactive, with no custom retry loop.
        with self._lock:
            self._ready()
            if self._auth is None:
                # The pinned SDK logs auth bodies and response tokens at DEBUG. Disable
                # its existing loggers, even when application/root logging is DEBUG.
                for name in list(logging.Logger.manager.loggerDict):
                    if name == "ssi_sdk" or name.startswith("ssi_sdk."):
                        logging.getLogger(name).disabled = True
                auth = Auth(Config(api_key=self._settings.ssi_api_key.get_secret_value(),
                                   api_secret=self._settings.ssi_api_secret.get_secret_value(),
                                   timeout=20, max_retries=1, retry_delay=2,
                                   rate_limit_per_second=100000 if self._transport is not None else 1,
                                   log_level="CRITICAL"))
                if self._transport is not None:
                    # SDK's public raw transport is used below; only test injection
                    # needs the pinned transport's httpx client customization.
                    import httpx
                    auth.rest_client._client = httpx.Client(
                        base_url=auth.config.api_url, transport=self._transport)
                self._auth = auth
            if self._auth.token is None:
                self._auth.authenticate()
            elif self._auth.is_token_expired:
                if self._auth.has_refresh_token:
                    self._auth.refresh()
                else:
                    self._auth.authenticate()
            return self._auth.rest_client.get(path, params=params)

    def _guard(self, symbol, operation, call):
        self._ready()
        try:
            return call()
        except Exception as exc:
            logger.warning("provider=ssi ticker=%s operation=%s error_type=%s",
                           symbol, operation, type(exc).__name__)
            raise ProviderError("SSI Market Data is temporarily unavailable. Please retry later.") from None

    @staticmethod
    def _symbol(symbol):
        value = symbol.strip().upper()
        return value if re.fullmatch(r"[A-Z0-9]{1,16}", value) else None

    @lru_cache(maxsize=512)
    def _security(self, symbol, bucket):
        def fetch():
            payload = self._request(EP_DATA_SECURITIES_BY_BOARD, {"symbol": symbol})
            # V3 returns HTTP 200 with code 204 for a verified no-content result.
            if isinstance(payload, dict) and payload.get("code") == 204 and not payload.get("data"):
                return None
            # V3 securities response is an array, not the OHLC pagination envelope.
            if not isinstance(payload, list):
                raise ValueError("Unexpected securities schema")
            if not payload:
                return None
            if len(payload) != 1 or not isinstance(payload[0], dict):
                raise ValueError("Unexpected securities result")
            row = payload[0]
            if row.get("symbol") != symbol or row.get("board") not in {"HOSE", "HNX", "UPCOM"}:
                raise ValueError("Unexpected security identity")
            name = row.get("symbolNameEn") or row.get("symbolNameVi")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Missing security identity")
            return name
        return self._guard(symbol, "security", fetch)

    def company_name(self, symbol):
        self._ready()
        symbol = self._symbol(symbol)
        return self._security(symbol, int(time.time() // 3600)) if symbol else None

    def validate_symbol(self, symbol):
        return self.company_name(symbol) is not None

    @lru_cache(maxsize=128)
    def _history(self, symbol, start, end, today, bucket):
        def fetch():
            first, last = daily_bounds(start, end)
            bars = {}
            for page in range(1, MAX_PAGES + 1):
                payload = self._request(EP_DATA_OHLC, {"symbol": symbol, "from": first,
                    "to": last, "timeFrame": "1d", "pageIndex": page, "pageSize": PAGE_SIZE})
                if isinstance(payload, dict) and payload.get("code") == 204 and not payload.get("data"):
                    return tuple(sorted(bars.values(), key=lambda bar: bar.date))
                if isinstance(payload, dict) and payload.get("code", 200) != 200:
                    raise ValueError("Upstream OHLC operation failed")
                if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                    raise ValueError("Unexpected OHLC schema")
                rows = payload["data"]
                for row in rows:
                    if not isinstance(row, dict) or row.get("symbol") != symbol:
                        raise ValueError("Unexpected OHLC identity")
                    day = datetime.strptime(row["tradingDate"], "%Y/%m/%d").date()
                    if not start <= day <= end or day >= today:
                        continue
                    bar = MarketBar(ticker=symbol, date=day, source=self.source,
                        **{key: numeric(row, key) for key in ("open", "high", "low", "close", "volume")})
                    if day in bars and bars[day] != bar:
                        raise ValueError("Conflicting duplicate date")
                    bars[day] = bar
                if not rows:
                    return tuple(sorted(bars.values(), key=lambda bar: bar.date))
            raise ValueError("Pagination safety bound exceeded")
        return self._guard(symbol, "history", fetch)

    def get_history(self, symbol, start, end):
        self._ready()
        symbol = self._symbol(symbol)
        if not symbol or start > end or (end - start).days > 730:
            raise ProviderError("Use a valid symbol and an ordered range of at most 730 days.")
        today = self._today()
        end = min(end, today - timedelta(days=1))
        if start > end:
            return []
        # Return copies so callers cannot mutate the cached canonical bars.
        return [bar.model_copy() for bar in self._history(symbol, start, end, today, int(time.time() // 300))]

    def get_latest(self, symbol):
        today = self._today()
        bars = self.get_history(symbol, today - timedelta(days=30), today)
        return bars[-1] if bars else None
