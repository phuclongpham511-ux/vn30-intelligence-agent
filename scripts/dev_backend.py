"""Existing main.app, isolated DEMO SQLite, no provider connections or collector.

Started by scripts/dev.mjs; stdin EOF shuts down this child gracefully.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import threading
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def validate_runtime(directory):
    directory = Path(directory).resolve(strict=True)
    base = (Path(os.environ.get('LOCALAPPDATA', os.environ.get('LocalAppData', __import__('tempfile').gettempdir()))) / 'Woofi' / 'Development').resolve()
    if directory.parent != base or not directory.name.startswith('run-'):
        raise ValueError('Expected a new launcher-owned development directory')
    manifest = json.loads((directory / 'identity.json').read_text())
    database = directory / 'development.sqlite'
    if (manifest['source'] != str(ROOT.resolve()) or manifest['contract'] != 'woofi-development-v1'
            or Path(manifest['database']).resolve() != database or database.exists() or database.is_symlink()
            or manifest['backend'] != 'http://127.0.0.1:8102'):
        raise ValueError('Invalid source/data binding or existing database; start a fresh run')
    return manifest, database


def seed_demo(session):
    """Same ingestion/search seams as offline news tests; supplied synthetic bytes only."""
    from src.models import Security, Stock
    from src.news.adapters import ArticleInput
    from src.news.registry import Source
    from src.news.service import ingest_cycle
    now = datetime.now(timezone.utc) - timedelta(minutes=5)
    for symbol, name in [('ABC', 'DEMO Example Technology Corporation'), ('XYZ', 'DEMO Example Steel Corporation')]:
        # Like existing offline tests, simulate the SSI identity contract inside
        # this DEMO-only DB. Never relax listed_equities' production source gate.
        session.add(Security(symbol=symbol, company_name=name, exchange='HOSE', last_synced_at=now))
        session.add(Stock(symbol=symbol, company_name=name, exchange='HOSE'))
    session.commit()
    source = Source(source_id='woofi-dev-demo', name='DEMO · Synthetic publisher',
        endpoint='https://woofi-development.example/rss', country='VN', language='vi', category='VN', publisher_group='woofi-dev-demo')
    incoming = [ArticleInput('VN-Index tăng nhờ cổ phiếu ABC · DEMO', 'https://woofi-development.example/market', now),
        ArticleInput('Ngành thép: cổ phiếu ABC, XYZ mở rộng xuất khẩu · DEMO', 'https://woofi-development.example/industry', now-timedelta(minutes=1)),
        ArticleInput('ABC công bố lợi nhuận quý III · DEMO', 'https://woofi-development.example/company', now-timedelta(minutes=2),
            text='DEMO Example Technology Corporation mở rộng trung tâm dữ liệu tại Việt Nam.', text_provenance='rss:description')]
    ingest_cycle(session, [source], now=now+timedelta(minutes=1), force=True, fetch=lambda _: incoming)


def install_io_guard(database):
    """Process-local defense: no outbound sockets, subprocesses, or other SQLite DBs."""
    def guard(event, args):
        if event in ('socket.connect', 'subprocess.Popen', 'os.system'):
            raise PermissionError('Development backend: external execution/connection disabled')
        if event == 'socket.getaddrinfo' and args[0] not in ('127.0.0.1', '::1', None):
            raise PermissionError('Development backend: external DNS disabled')
        if event == 'sqlite3.connect' and Path(str(args[0])).resolve() != database.resolve():
            raise PermissionError('Development backend: only its isolated SQLite database is allowed')
    sys.addaudithook(guard)


def run(directory):
    manifest, database = validate_runtime(directory)
    actual_sha = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    if actual_sha != manifest['source_sha']:
        raise ValueError('Worktree commit changed during startup; restart development')
    # Do not load source .env files or inherit optional financial/credential paths.
    from src.config import settings
    configured = settings.Settings(_env_file=None, database_url='sqlite:///' + database.as_posix(),
        app_env='development', market_data_provider='disabled-development', technical_eod_pilot=False,
        ssi_api_key='', ssi_api_secret='', openai_api_key='')
    settings.get_settings = lambda: configured
    from main import app
    import main
    if Path(main.__file__).resolve() != ROOT / 'main.py':
        raise ValueError('Unexpected backend source module')
    from src.services import stocks, data, live_market
    from src.providers.base import ProviderNotReadyError
    def unavailable():
        raise ProviderNotReadyError('DEMO development: live providers are disabled')
    for dependency in (stocks.get_market_provider, data.get_fundamental_provider, data.get_news_provider, live_market.get_live_market):
        app.dependency_overrides[dependency] = unavailable
    from fastapi.responses import JSONResponse
    @app.middleware('http')
    async def boundary(request, call_next):
        allowed_hosts = {'127.0.0.1:8102'}
        if (request.client.host != '127.0.0.1' or request.headers.get('host') not in allowed_hosts
                or request.headers.get('origin') not in (None, 'http://127.0.0.1:8102')
                or request.headers.get('sec-fetch-site') not in (None, 'same-origin', 'none')):
            return JSONResponse({'detail':'Local development only'}, status_code=403)
        if request.url.path == '/__woofi_dev__/identity':
            return JSONResponse(manifest)
        if request.url.path.startswith(('/personal-research', '/financial-intelligence', '/ingestion')) or request.url.path.endswith('/refresh'):
            return JSONResponse({'detail':'Disabled in synthetic development'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Woofi-Development-Run'] = manifest['run_id']
        return response
    original_lifespan = app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(application):
        # Event loop is already created: its Windows self-pipe is not provider traffic.
        install_io_guard(database)
        async with original_lifespan(application):
            from sqlmodel import Session
            from src.db.session import get_engine
            with Session(get_engine()) as session:
                seed_demo(session)
            yield
    app.router.lifespan_context = lifespan
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8102, proxy_headers=False, access_log=False))
    def parent_lifetime():
        sys.stdin.buffer.read()
        server.should_exit = True
    threading.Thread(target=parent_lifetime, daemon=True).start()
    server.run()


if __name__ == '__main__':
    run(sys.argv[1])
