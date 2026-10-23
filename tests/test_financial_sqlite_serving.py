import json
import hashlib
import pytest
from fastapi.testclient import TestClient
from src.services.financial_journal import MetricJournal
from src.services.personal_financials import sqlite_research_packet,configured_research_packet,personal_projection
from src.analytics.financial_engine import financial_engine
from test_financial_storage import history_packet


def stable(value):
    data=value.model_dump(mode='json') if hasattr(value,'model_dump') else dict(value)
    data.pop('read_at',None)
    return data


@pytest.fixture
def stored(tmp_path):
    journal=MetricJournal(tmp_path/'financial.sqlite');journal.initialize()
    packet=history_packet()
    capture=journal.import_packet(packet,'a'*64)
    return journal,packet,capture


def test_whole_revision_roundtrip_and_34_quarter_engine_hierarchy_parity(stored):
    j,p,c=stored
    digest=hashlib.sha256(j.path.read_bytes()).hexdigest()
    read,sha=sqlite_research_packet(j.path,'ABC',frequency='quarterly')
    assert read==p and sha=='a'*64
    assert len(read.reports['income'].observations)==37
    for frequency in ('annual','quarterly','ttm'):
        assert stable(financial_engine(read,frequency=frequency,limit=40))==stable(financial_engine(p,frequency=frequency,limit=40))
        assert stable(personal_projection(read,frequency=frequency,limit=34,authorization_reference='synthetic'))==stable(personal_projection(p,frequency=frequency,limit=34,authorization_reference='synthetic'))
    assert hashlib.sha256(j.path.read_bytes()).hexdigest()==digest


def test_conflicting_revisions_require_explicit_capture_and_preserve_history(stored,tmp_path):
    j,p,c=stored
    short=history_packet(quarters=4,marker=2)
    newer=j.import_packet(short,'b'*64)
    with pytest.raises(ValueError,match='Ambiguous'):
        sqlite_research_packet(j.path,'ABC')
    assert sqlite_research_packet(j.path,'ABC',capture_id=c['capture_id'])[0]==p
    assert sqlite_research_packet(j.path,'ABC',capture_id=newer['capture_id'],source=p.source)[0]==short
    (tmp_path/'index.json').write_text(json.dumps(dict(contract='personal-saved-captures-v1',captures={'ABC':dict(sha256='a'*64,file='missing.json')})))
    assert sqlite_research_packet(j.path,'ABC',capture_directory=tmp_path)[0]==p


@pytest.mark.parametrize('kwargs',[dict(ticker='XYZ'),dict(ticker='ABC',source='missing'),dict(ticker='ABC',capture_id='0'*64)])
def test_missing_selection_never_falls_back_to_another_revision(stored,kwargs):
    with pytest.raises(FileNotFoundError):sqlite_research_packet(stored[0].path,**kwargs)


def test_invalid_database_never_creates_or_initializes_a_file(tmp_path):
    missing=tmp_path/'missing.sqlite'
    with pytest.raises(ValueError):sqlite_research_packet(missing,'ABC')
    assert not missing.exists()
    bad=tmp_path/'bad.sqlite';bad.write_bytes(b'not sqlite')
    import sqlite3
    with pytest.raises(sqlite3.DatabaseError):sqlite_research_packet(bad,'ABC')


def environment(monkeypatch,journal,tmp_path):
    for k,v in dict(APP_ENV='development',DATABASE_URL='sqlite://',WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1',WOOFI_PERSONAL_FINANCIAL_READS='sqlite',
        WOOFI_PERSONAL_SQLITE=str(journal.path),WOOFI_PERSONAL_CAPTURES=str(tmp_path)).items():monkeypatch.setenv(k,v)


def test_private_api_preserves_contract_gates_and_database_failure(stored,tmp_path,monkeypatch):
    j,p,c=stored;environment(monkeypatch,j,tmp_path)
    from main import app
    client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
    result=client.get('/personal-research/financials/ABC?frequency=quarterly')
    assert result.status_code==200 and len(result.json()['rows'])==34
    assert result.headers['cache-control']=='private, no-store'
    expected=personal_projection(p,frequency='quarterly',limit=34,authorization_reference='task:financial-v6-personal-research:'+'a'*64)
    assert stable(result.json())==stable(expected)
    assert client.get('/personal-research/financials/XYZ').status_code==404
    monkeypatch.setenv('WOOFI_PERSONAL_SQLITE',str(tmp_path/'absent.sqlite'))
    assert client.get('/personal-research/financials/ABC').status_code==503
    monkeypatch.setenv('APP_ENV','production')
    assert client.get('/personal-research/financials/ABC').status_code==404


def test_flag_default_capture_rollback_and_production_denial(stored,tmp_path,monkeypatch):
    j,p,c=stored;environment(monkeypatch,j,tmp_path)
    monkeypatch.setenv('APP_ENV','production')
    with pytest.raises(ValueError):configured_research_packet(tmp_path,'ABC')
    monkeypatch.setenv('APP_ENV','development')
    monkeypatch.setenv('WOOFI_PERSONAL_FINANCIAL_READS','captures')
    monkeypatch.setattr('src.services.personal_financials.saved_research_packet',lambda *a,**kw:(p,'a'*64))
    assert configured_research_packet(tmp_path,'ABC')[0]==p
    monkeypatch.delenv('WOOFI_PERSONAL_FINANCIAL_READS')
    assert configured_research_packet(tmp_path,'ABC')[0]==p


def test_selected_original_survives_ambiguous_optional_provider(stored,tmp_path,monkeypatch):
    from src.providers.reviewed_reports import report_packet
    from test_free_financial_sources import reviewed
    j,p,c=stored
    j.import_packet(history_packet(marker=2),'b'*64)
    original,_=report_packet(reviewed(tmp_path),tmp_path)
    capture=j.import_packet(original,'c'*64)
    environment(monkeypatch,j,tmp_path)
    from main import app
    client=TestClient(app,client=('127.0.0.1',1234),base_url='http://127.0.0.1')
    response=client.get('/personal-research/financials/ABC?capture_id='+capture['capture_id'])
    assert response.status_code==200
    assert response.json()['source']==original.source


def test_explicit_capture_does_not_load_an_unselected_corrupt_packet(stored):
    j,p,c=stored
    other=j.import_packet(history_packet(marker=2),'b'*64)
    with j.connect() as db,db:
        db.execute('update financial_capture set packet_sha256=? where id=?',('0'*64,other['capture_id']))
    assert sqlite_research_packet(j.path,'ABC',capture_id=c['capture_id'])[0]==p
