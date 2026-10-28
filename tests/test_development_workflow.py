"""Development boundary tests using synthetic inputs and subprocess isolation."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from scripts.dev_backend import ROOT, seed_demo, validate_runtime


def test_synthetic_development_uses_real_search_and_category_routes(session, client):
    seed_demo(session)
    rows = client.get('/news/feed/page?research_category=ALL&q=ABC').json()['items']
    assert len(rows) == 3
    assert all('DEMO' in row['representative_article']['title'] for row in rows)
    assert {row['research_category'] for row in rows} == {'COMPANY','INDUSTRY','MARKET_BRIEF'}
    assert len(client.get('/news/feed/page?research_category=INDUSTRY&q=ABC').json()['items']) == 1
    assert len(client.get('/news/feed/page', params={'research_category':'ALL','q':'trung tâm dữ liệu'}).json()['items']) == 1
    assert client.get('/news/feed/page?research_category=ALL&q=unmatched').json()['items'] == []
    assert client.get('/health').status_code == 200
    assert client.get('/stocks').status_code == 200


def test_runtime_must_be_new_owned_directory_and_bind_to_this_source(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    directory=tmp_path/'Woofi'/'Development'/'run-test';directory.mkdir(parents=True)
    manifest=dict(source=str(ROOT.resolve()),contract='woofi-development-v1',
        database=str(directory/'development.sqlite'),backend='http://127.0.0.1:8102')
    file=directory/'identity.json';file.write_text(json.dumps(manifest))
    assert validate_runtime(directory)[1] == directory/'development.sqlite'
    manifest['database']=str(tmp_path/'canonical.sqlite');file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):validate_runtime(directory)
    manifest['database']=str(directory/'development.sqlite');file.write_text(json.dumps(manifest))
    (directory/'development.sqlite').touch()
    with pytest.raises(ValueError):validate_runtime(directory)
    with pytest.raises(ValueError):validate_runtime(tmp_path)


def test_backend_io_guard_blocks_network_and_other_databases_before_access(tmp_path):
    # Install irreversible audit hook only in a disposable test process.
    code = '''
from pathlib import Path
import socket, sqlite3, sys
from scripts.dev_backend import install_io_guard
database=Path(sys.argv[1]); install_io_guard(database)
sqlite3.connect(str(database)).close()
for action in [lambda: sqlite3.connect(str(database.parent/'forbidden.sqlite')),
               lambda: socket.socket().connect(('127.0.0.1',8000)),
               lambda: socket.getaddrinfo('example.com',443)]:
    try: action()
    except PermissionError: pass
    else: raise AssertionError('guard failed')
print('PASS')
'''
    result=subprocess.run([sys.executable,'-c',code,str(tmp_path/'development.sqlite')],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'PASS' in result.stdout
    assert not (tmp_path/'forbidden.sqlite').exists()
