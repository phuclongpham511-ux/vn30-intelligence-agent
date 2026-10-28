"""HTTP seam with persisted synthetic operational evidence; not live SSI proof."""
from copy import deepcopy
from datetime import date, timedelta, datetime, timezone
import json
import pytest
from sqlalchemy import event
from test_d1_runtime import snapshot,bb_snapshot,NOW
from test_d4_runtime import data_with_tail
from test_eod_readiness import modern,proof
from test_technical_eod_consumer import metadata
from main import app
from routers.technical import get_local_evidence_reader,get_evaluation_clock,get_request_budget
from src.services.technical_api import LocalEvidenceReader,TechnicalRequestBudget


@pytest.fixture
def api(client,session,tmp_path,monkeypatch):
    metadata(session)
    reader=LocalEvidenceReader(tmp_path/'operational')
    app.dependency_overrides[get_local_evidence_reader]=lambda:reader
    app.dependency_overrides[get_evaluation_clock]=lambda:NOW
    app.dependency_overrides[get_request_budget]=lambda:TechnicalRequestBudget(max_requests=100)
    acquisitions=[]
    def forbidden(*args,**kwargs):
        acquisitions.append(1)
        raise AssertionError('External acquisition during Technical HTTP read')
    monkeypatch.setattr('src.services.technical_eod.read_eod_history',forbidden)
    monkeypatch.setattr('src.services.stocks.get_market_provider',forbidden)
    monkeypatch.setattr('src.providers.ssi.SsiMarketDataProvider._request',forbidden)
    monkeypatch.setattr('scripts.ingest_data.run_once',forbidden,raising=False)
    monkeypatch.setattr('httpx.HTTPTransport.handle_request',forbidden)
    monkeypatch.setattr('requests.Session.request',forbidden)
    yield client,session,reader
    assert not acquisitions


def persist(api,data=None,read=None,calendar=None):
    client,session,reader=api
    data,base_read,base_cal=modern(data)
    read=read or base_read
    calendar=base_cal if calendar is None else calendar
    target=data['calendar'][-1]
    path=reader.directory/'XYZ'/f'{target}.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=dict(schema_version='operational-technical-evidence-v1',history_start=data['calendar'][0],
        history=read.model_dump(mode='json'),calendar=calendar.model_dump(mode='json'))
    path.write_text(json.dumps(payload),encoding='utf-8')
    return target,path,payload


def get(api,target='2020-03-02',ticker='XYZ',extra=''):
    return api[0].get(f'/technical/{ticker}/daily?session={target}'+extra)


@pytest.mark.parametrize('count',[0,1,2])
def test_real_persisted_consumer_zero_one_two_events(api,count):
    data=snapshot(returns=[.01]*60+[0 if count==0 else .1],
                  volumes=[100]*61+[200 if count==2 else 50])
    target,_,_=persist(api,data)
    response=get(api,target,ticker='xyz')
    assert response.status_code==200
    body=response.json()
    assert body['kind']=='packet' and body['safe_to_display_as_verified'] is True
    packet=body['packet']
    assert packet['ticker']=='XYZ' and packet['trading_session']==target
    assert len(packet['top_insights'])==count
    assert packet['packet_state']==('HAS_INSIGHTS' if count else 'NO_MEANINGFUL_TECHNICAL_CHANGE')
    assert packet['score_version']=='v0'
    assert 'source_receipt_not_certified_historical_vendor_vintage' in packet['limitations']
    assert all(e['corporate_action_context']['status']=='UNKNOWN' for e in packet['top_insights'])


@pytest.mark.parametrize('overflow',[False,True])
def test_three_and_overflow_preserve_real_episode_ranking(api,monkeypatch,overflow):
    data=bb_snapshot() if overflow else data_with_tail([.1,.1],[200,200])
    if overflow: data['bars'][-1].update(open=106,close=106,high=106.1)
    import src.materiality.factual as factual
    original=factual.technical_history
    def controlled(ticker,bars,source):
        rows=original(ticker,bars,source)
        for row in rows[-2:]:
            final=row.date.isoformat()==data['calendar'][-1]
            if row.ma50 is not None: row.ma20=row.ma50+(1 if final else -1)
            if overflow: row.rsi14=71 if final else 70
        return rows
    monkeypatch.setattr(factual,'technical_history',controlled)
    target,_,_=persist(api,data)
    body=get(api,target).json()
    assert body['kind']=='packet'
    packet=body['packet']
    assert len(packet['top_insights'])==3
    assert len(packet['all_current_session_events'])==(5 if overflow else 3)
    assert len(packet['overflow_event_ids'])==(2 if overflow else 0)
    assert packet['ranked_eligible_event_ids'][:3]==[e['event_id'] for e in packet['top_insights']]
    assert all(e['evidence_refs'] and e['provenance'] for e in packet['top_insights'])
    if not overflow:
        volume=next(e for e in packet['all_current_session_events'] if e['event_type']=='unusual_volume')
        assert volume['episode_id'] and volume['episode_status']=='CONTINUATION'


def test_missing_local_history_has_safe_typed_diagnostic(api):
    body=get(api).json()
    assert body['kind']=='diagnostic' and body['readiness_status']=='INCOMPLETE_EVIDENCE'
    assert body['reason_codes']==['missing_local_history']
    assert 'local_history' in body['missing_evidence']
    assert body['safe_to_display_as_verified'] is False
    assert body['source_last_observed_at'] is None
    assert 'packet' not in body and 'NO_MEANINGFUL_TECHNICAL_CHANGE' not in json.dumps(body)


@pytest.mark.parametrize('mode,status',[('syntax',422),('unknown',404),('venue',422),('date',422),('future',422),('asof',422),('forge',422)])
def test_request_validation(api,mode,status):
    from src.models import Security
    ticker='!' if mode=='syntax' else 'UNKNOWN' if mode=='unknown' else 'XYZ'
    target='bad' if mode=='date' else '2021-01-02' if mode=='future' else '2020-03-02'
    extra='&as_of=2020-01-01T00:00:00Z' if mode=='asof' else '&completion_status=COMPLETE' if mode=='forge' else ''
    if mode=='venue':
        row=api[1].get(Security,'XYZ');row.exchange='OTHER';api[1].commit()
    assert get(api,target,ticker,extra).status_code==status


@pytest.mark.parametrize('mode',['lookback','calendar','completion','basis','provenance','late','continuity','closed'])
def test_missing_evidence_never_returns_success_packet(api,mode):
    data,read,cal=modern(snapshot(15) if mode=='lookback' else None)
    if mode=='completion': read=read.model_copy(update={'completion_evidence':()})
    if mode=='basis': read=read.model_copy(update={'volume_unit':'lots'})
    if mode=='late': read=read.model_copy(update={'observed_at':NOW+timedelta(hours=1)})
    if mode=='continuity': cal=cal.model_copy(update={'records':tuple(r for r in cal.records if r!=cal.records[-2])})
    if mode=='closed': cal=cal.model_copy(update={'records':cal.records[:-1]+(cal.records[-1].model_copy(update={'status':'CLOSED'}),)})
    if mode=='provenance': read=read.model_copy(update={'source_version':'C:\\private\\secret.env'})
    target,path,payload=persist(api,data,read,cal)
    if mode=='calendar': payload['calendar']=None;path.write_text(json.dumps(payload),encoding='utf-8')
    response=get(api,target)
    assert response.status_code==200
    body=response.json()
    assert body['kind']=='diagnostic' and body['safe_to_display_as_verified'] is False
    assert body['reason_codes'] and body['missing_evidence']
    assert 'packet' not in body and 'private' not in response.text


def test_verified_same_day_accepted_with_server_clock(api):
    data,read,cal=modern()
    target=read.observations[-1].payload.date
    cutoff=datetime.combine(target,datetime.min.time(),timezone(timedelta(hours=7)))+timedelta(hours=16)
    receipt=cutoff-timedelta(minutes=1)
    read=read.model_copy(update={'observed_at':receipt})
    final=read.observations[-1].model_copy(update={'available_at':receipt,'availability_basis':'published'})
    read=read.model_copy(update={'observations':read.observations[:-1]+(final,),
        'completion_evidence':(proof(read,final.payload,receipt),)})
    cal=cal.model_copy(update={'records':tuple(r.model_copy(update={'observed_at':receipt}) for r in cal.records)})
    from src.models import Security
    row=api[1].get(Security,'XYZ');row.last_synced_at=receipt-timedelta(days=1);api[1].commit()
    app.dependency_overrides[get_evaluation_clock]=lambda:cutoff
    target,_,_=persist(api,data,read,cal)
    response=get(api,target)
    assert response.status_code==200 and response.json()['kind']=='packet'
    assert response.json()['packet']['evaluation_as_of']==cutoff.astimezone(timezone.utc).isoformat().replace('+00:00','Z')


def test_no_network_worker_writes_and_deterministic_repeat(api):
    target,_,_=persist(api)
    statements=[]
    def capture(conn,cursor,statement,parameters,context,executemany): statements.append(statement)
    engine=api[1].get_bind()
    event.listen(engine,'before_cursor_execute',capture)
    try:
        first=get(api,target)
        second=get(api,target)
        assert first.json()==second.json()
        assert first.status_code==200 and first.json()['kind']=='packet'
    finally: event.remove(engine,'before_cursor_execute',capture)
    assert statements and all(s.lstrip().upper().startswith('SELECT') for s in statements)
    assert all('LIMIT' in s.upper() or 'security' in s.lower() for s in statements)


@pytest.mark.parametrize('mode',['malformed','oversized','path','exception'])
def test_bad_local_access_sanitized(api,mode,monkeypatch):
    target,path,payload=persist(api)
    if mode=='malformed': path.write_text('token=SECRET C:\\private\\file',encoding='utf-8')
    if mode=='oversized': path.write_bytes(b' '* (4*1024*1024+1))
    if mode=='path': payload['calendar']['records'][0]['source_ref']='C:\\private\\file';path.write_text(json.dumps(payload),encoding='utf-8')
    if mode=='exception': monkeypatch.setattr(api[2],'read',lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('token=SECRET C:\\private\\file')))
    response=get(api,target)
    assert response.status_code==(503 if mode=='exception' else 200)
    body=response.json()
    assert body['kind']=='diagnostic' and body['safe_to_display_as_verified'] is False
    assert 'SECRET' not in response.text and 'private' not in response.text and 'Traceback' not in response.text


def test_public_budget_limits_calculation_before_local_read(api,monkeypatch):
    budget=TechnicalRequestBudget(max_requests=1)
    app.dependency_overrides[get_request_budget]=lambda:budget
    assert get(api).status_code==200
    monkeypatch.setattr(api[2],'read',lambda *a:pytest.fail('read after budget exhausted'))
    response=get(api)
    assert response.status_code==429 and response.headers['Retry-After']
    assert response.json()['safe_to_display_as_verified'] is False


def test_busy_budget_does_not_queue_calculations(api,monkeypatch):
    budget=TechnicalRequestBudget()
    app.dependency_overrides[get_request_budget]=lambda:budget
    assert budget.enter()==0
    try:
        monkeypatch.setattr(api[2],'read',lambda *a:pytest.fail('read while busy'))
        assert get(api).status_code==429
    finally: budget.exit()


def test_corporate_action_context_keeps_scores_and_order(api):
    from src.corporate_actions.models import CorporateActionNotice
    from src.corporate_actions.repository import CorporateActionRepository
    target,_,_=persist(api)
    before=get(api,target).json()['packet']
    notice=CorporateActionNotice(symbol='XYZ',action_type='cash_dividend',
        effective_date=date.fromisoformat(target),source='curated_verified',source_id='action-1',verified=True)
    CorporateActionRepository(api[1]).ingest(notice,received_at=NOW-timedelta(hours=1))
    after=get(api,target).json()['packet']
    assert before['ranked_eligible_event_ids']==after['ranked_eligible_event_ids']
    for old,new in zip(before['top_insights'],after['top_insights']):
        assert (old['base_v0'],old['significance_v0'],old['novelty_v0'],old['confidence_v0'])==(
            new['base_v0'],new['significance_v0'],new['novelty_v0'],new['confidence_v0'])
        assert new['corporate_action_context']['status']=='KNOWN_MATCH'
        assert new['corporate_action_context']['coverage']=='INCOMPLETE'


def test_bounded_ca_reader_preserves_symbol_date_corrections_and_cutoff(api):
    from src.corporate_actions.models import CorporateActionNotice
    from src.corporate_actions.repository import CorporateActionRepository
    from src.services.technical_api import BoundedCorporateActionReader
    repo=CorporateActionRepository(api[1])
    notice=CorporateActionNotice(symbol='XYZ',action_type='cash_dividend',
        effective_date=date(2020,3,2),source='curated_verified',source_id='revision',component_id='dividend',verified=True)
    repo.ingest(notice,received_at=NOW-timedelta(hours=3))
    repo.ingest(notice.model_copy(update={'symbol':'ABC'}),received_at=NOW-timedelta(hours=2))
    repo.ingest(notice,received_at=NOW+timedelta(hours=1))
    bounded=BoundedCorporateActionReader(api[1],'XYZ',NOW)
    assert bounded.context_for('XYZ',date(2020,3,2),as_of=NOW)==repo.context_for('XYZ',date(2020,3,2),as_of=NOW)
    assert bounded.get_known_actions_as_of(as_of=NOW)[0].symbol=='ABC'


@pytest.mark.parametrize('mode',['fixture','hash','unit','source','metadata_late','calendar_late','proof_late','missing_target','bound'])
def test_other_critical_gates(api,mode):
    data,read,cal=modern()
    if mode=='fixture': read=read.model_copy(update={'is_fixture':True})
    if mode=='hash':
        proofs=list(read.completion_evidence)
        proofs[-1]=proofs[-1].model_copy(update={'bar_sha256':'0'*64})
        read=read.model_copy(update={'completion_evidence':tuple(proofs)})
    if mode=='unit': read=read.model_copy(update={'price_unit':'thousand_VND'})
    if mode=='source': read=read.model_copy(update={'source':'OTHER'})
    if mode=='calendar_late': cal=cal.model_copy(update={'records':tuple(r.model_copy(update={'observed_at':NOW+timedelta(hours=1)}) for r in cal.records)})
    if mode=='proof_late': read=read.model_copy(update={'completion_evidence':tuple(p.model_copy(update={'observed_at':NOW+timedelta(hours=1)}) for p in read.completion_evidence)})
    if mode=='missing_target': read=read.model_copy(update={'observations':read.observations[:-1]})
    if mode=='bound': read=read.model_copy(update={'observations':read.observations*10})
    if mode=='metadata_late':
        from src.models import Security
        row=api[1].get(Security,'XYZ');row.last_synced_at=NOW+timedelta(hours=1);api[1].commit()
    target,_,_=persist(api,data,read,cal)
    response=get(api,target)
    assert response.status_code==200
    assert response.json()['kind']=='diagnostic' and response.json()['safe_to_display_as_verified'] is False


def test_valid_events_preserve_noncritical_unresolved_checks(api):
    target,_,_=persist(api)
    packet=get(api,target).json()['packet']
    assert packet['top_insights']
    assert 'bounded_episode_history_unverified_left_boundary' in packet['limitations']
    assert any(e['episode_relationship']=='UNRESOLVED' for e in packet['all_current_session_events'])


@pytest.mark.parametrize('extra',['&session=2020-03-02','&history_start=2020-01-01','&evidence=COMPLETE'])
def test_cannot_supply_internal_inputs_or_duplicate_session(api,extra):
    assert get(api,extra=extra).status_code==422


def test_database_failure_is_503_without_exception_text(api,monkeypatch):
    monkeypatch.setattr(api[1],'get',lambda *a:(_ for _ in ()).throw(RuntimeError('API_SECRET=SECRET C:\\private\\db')))
    response=get(api)
    assert response.status_code==503
    assert response.json()['readiness_status']=='INFRASTRUCTURE_FAILURE'
    assert 'SECRET' not in response.text and 'private' not in response.text


def test_private_ca_provenance_rejects_packet_without_redacting_evidence(api):
    from src.corporate_actions.models import CorporateActionNotice
    from src.corporate_actions.repository import CorporateActionRepository
    target,_,_=persist(api)
    notice=CorporateActionNotice(symbol='XYZ',action_type='cash_dividend',
        effective_date=date.fromisoformat(target),source='curated_verified',source_id='action-private',verified=True,
        verification_note='C:\\private\\operator.txt')
    CorporateActionRepository(api[1]).ingest(notice,received_at=NOW-timedelta(hours=1))
    response=get(api,target)
    assert response.json()['kind']=='diagnostic' and 'invalid_provenance' in response.json()['reason_codes']
    assert 'private' not in response.text


def test_failed_optional_ca_read_is_bounded_once(api,monkeypatch):
    from src.services.technical_api import BoundedCorporateActionReader
    reader=BoundedCorporateActionReader(api[1],'XYZ',NOW)
    attempts=[]
    def fail(*args,**kwargs):
        attempts.append(1)
        raise RuntimeError('optional source unavailable')
    monkeypatch.setattr(api[1],'exec',fail)
    with pytest.raises(RuntimeError): reader.get_known_actions_as_of(as_of=NOW)
    with pytest.raises(ValueError): reader.get_known_actions_as_of(as_of=NOW)
    assert len(attempts)==1


@pytest.mark.parametrize('reference',['file:///private/proof.json','https://public.example/proof?token=SECRET','https://[bad'])
def test_unsafe_evidence_references_are_domain_diagnostics(api,reference):
    target,path,payload=persist(api)
    payload['calendar']['records'][0]['source_ref']=reference
    path.write_text(json.dumps(payload),encoding='utf-8')
    response=get(api,target)
    assert response.status_code==200 and response.json()['kind']=='diagnostic'
    assert 'SECRET' not in response.text and reference not in response.text


def test_verified_packet_is_exact_consumer_output(api):
    from src.services.technical_eod import evaluate_technical_eod_packet
    from src.services.technical_api import BoundedCorporateActionReader
    target,_,_=persist(api)
    evidence=api[2].read('XYZ',date.fromisoformat(target))
    expected=evaluate_technical_eod_packet('XYZ',target,evaluation_as_of=NOW,generated_at=NOW,
        db_session=api[1],history_read=evidence.history,calendar=evidence.calendar,
        history_start=evidence.history_start,corporate_actions=BoundedCorporateActionReader(api[1],'XYZ',NOW))
    assert get(api,target).json()['packet']==expected.model_dump(mode='json')
