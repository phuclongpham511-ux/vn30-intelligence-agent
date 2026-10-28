"""Bounded synthetic ASGI/cache timings, plus optional saved-public-response replay.

No listening server, production database, collector or provider acquisition.
Run from repo root with --output <new-json-path>. Results are not browser timings.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import socket
from statistics import median
from threading import Event
import time
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--replay-json')
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error('Refuse to overwrite benchmark evidence')
    os.environ.update(APP_ENV='production', DATABASE_URL='sqlite://', SSI_API_KEY='',
        SSI_API_SECRET='', OPENAI_API_KEY='', PYTHONDONTWRITEBYTECODE='1')
    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, create_engine
    from main import app
    from src.db.session import create_tables, get_session
    from src.models import Security
    from src.providers.vnstock import VnstockFundamentalDataProvider
    from src.providers.base import ProviderNotReadyError
    from src.services.data import get_fundamental_provider
    from src.services.stocks import get_market_provider
    from src.services.live_market import get_live_market
    from src.schemas.financials import FinancialEngineResponse
    fixture = runpy.run_path(str(Path('tests/test_financial_engine.py')))['packet']()
    result = {'evidence_kind': 'SYNTHETIC', 'provider_delay_ms': 250,
        'browser_render_hydration': 'NOT_VERIFIED', 'authenticated_provider_calls': 0}
    calls = []
    entered = Event()
    def fetch(symbol, sdk):
        calls.append(symbol)
        if symbol == 'COLD':
            entered.set()
            time.sleep(.25)
        return fixture
    with patch('src.providers.vnstock.financial_packet.fetch_packet', fetch):
        provider = VnstockFundamentalDataProvider()
        provider.get_reports('WARM')
        with ThreadPoolExecutor(max_workers=2) as pool:
            cold = pool.submit(provider.get_reports, 'COLD')
            assert entered.wait(2)
            start = time.perf_counter()
            provider.get_reports('WARM')
            result['warm_cache_during_cold_read_ms'] = (time.perf_counter()-start)*1000
            cold.result(timeout=3)
        result['packet_reads'] = calls
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    create_tables(engine)
    with Session(engine) as db:
        db.add(Security(symbol='ABC', exchange='HOSE', company_name='Synthetic issuer',
            source='Synthetic:metadata', last_synced_at=datetime.now(timezone.utc), search_text='abc synthetic issuer'))
        db.commit()
    def session():
        with Session(engine) as db:
            yield db
    class Financial:
        source = 'test:VCI'
        def get_reports(self, symbol): return fixture.model_copy(deep=True)
    class Market:
        source = 'Synthetic:no-provider'
        def validate_symbol(self, symbol): return True
        def get_history(self, *args): return []
    class Live:
        def index(self): return {'snapshot':None, 'status':'unavailable', 'session':'unknown', 'as_of':None}
        def read(self, symbols, **kwargs): return {'items':{s:{'status':'unavailable','snapshot':None} for s in symbols},'session':'unknown','as_of':None}
        def close(self): pass
    app.dependency_overrides[get_session] = session
    app.dependency_overrides[get_market_provider] = Market
    app.dependency_overrides[get_fundamental_provider] = Financial
    app.dependency_overrides[get_live_market] = Live
    routes = [
        ('Home', 'GET', '/stocks/live-index', None),
        ('Explore', 'GET', '/stocks/universe?q=ABC&limit=3', None),
        ('Stock Detail', 'GET', '/stocks/ABC/technical-history', None),
        ('Fundamentals full', 'GET', '/stocks/ABC/financials?limit=8', None),
        ('Fundamentals display', 'GET', '/stocks/ABC/financials?limit=8&projection=display', None),
        ('News', 'GET', '/news/feed?limit=3', None),
        ('Watchlist', 'POST', '/watchlists/intelligence', {'symbols':['ABC']}),
    ]
    result['isolated_api'] = {}
    try:
        # Any accidental provider network path is a benchmark failure.
        connect = socket.socket.connect
        def local_only(sock, address):
            # Windows asyncio uses an internal loopback socketpair.
            if address[0] not in ('127.0.0.1', '::1'):
                raise AssertionError('External network forbidden')
            return connect(sock, address)
        with patch('src.db.session.get_engine', lambda: engine), patch('socket.socket.connect', local_only), TestClient(app) as client:
            for name, method, url, body in routes:
                samples = []
                for _ in range(5):
                    start = time.perf_counter()
                    response = client.request(method, url, json=body)
                    samples.append((time.perf_counter()-start)*1000)
                    assert response.status_code == 200, (name, response.status_code, response.text[:120])
                result['isolated_api'][name] = {'median_ms':median(samples), 'samples_ms':samples,
                    'response_bytes':len(response.content), 'coverage':'small synthetic cache / empty unavailable source state'}
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
    if args.replay_json:
        source = Path(args.replay_json)
        if source.suffix != '.json' or source.stat().st_size > 16_000_000:
            parser.error('Replay accepts only a bounded saved financial JSON response')
        value = FinancialEngineResponse.model_validate_json(source.read_text(encoding='utf-8'))
        before = value.model_dump_json()
        try:
            from src.services.financial_presentation import display_financial_response
            display = display_financial_response(value)
        except ImportError:
            display = value
        samples = []
        for _ in range(5):
            start = time.perf_counter(); display.model_dump_json(); samples.append((time.perf_counter()-start)*1000)
        result['saved_financial_response_replay'] = {'evidence_kind':'REPLAY_OF_SAVED_PUBLIC_VCI_RESPONSE',
            'ticker':value.ticker, 'period_type':value.period_type, 'full_bytes':len(before.encode()),
            'display_bytes':len(display.model_dump_json().encode()), 'display_serialization_median_ms':median(samples),
            'new_provider_calls':0}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
