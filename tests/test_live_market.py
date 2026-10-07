from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.providers.ssi.live import normalize_trade, session_state
from src.providers.ssi.live import SsiLiveMarket, normalize_symbols
from src.providers.ssi.live import source_fresh
from src.providers.ssi import SsiMarketDataProvider
from src.config.settings import Settings
import httpx

VN = ZoneInfo('Asia/Ho_Chi_Minh')


def test_trade_uses_same_day_reference_and_preserves_missing_value():
    now = datetime(2026, 10, 7, 10, 8, 35, tzinfo=VN)
    row = normalize_trade({'s': 'FPT', 't': '2026/10/07 10:08:32',
                           'p': '60300', 'v': '1200'}, 60400, now)
    assert row['last_price'] == 60300
    assert row['reference_price'] == 60400
    assert row['change'] == -100
    assert row['change_percent'] == pytest.approx(-0.1655629139)
    assert row['total_volume'] == 1200
    assert row['total_value'] is None
    assert row['updated_at'] == '2026-10-07T10:08:32+07:00'
    assert row['open'] is None


@pytest.mark.parametrize('hour,minute,day,expected', [
    (10,0,7,'active'), (12,0,7,'break'), (14,0,7,'active'),
    (16,0,7,'closed'), (8,0,7,'closed'), (10,0,10,'closed')])
def test_session_uses_vietnam_clock_and_requires_trading_day_evidence(hour, minute, day, expected):
    now = datetime(2026,10,day,hour,minute,tzinfo=VN)
    assert session_state(now, confirmed_day=now.date()) == expected
    if expected == 'active':
        assert session_state(now, confirmed_day=None) == 'unknown'


@pytest.mark.parametrize('field,value', [('p','NaN'),('p',0),('p',False),('v',-1),('o','oops'),
    ('h','inf'),('t',None),('t','2026/10/08 10:00:00'),('s','FPT/../../')])
def test_malformed_source_trade_is_rejected(field, value):
    row = {'s':'FPT','t':'2026/10/07 10:08:32','p':60300,'v':1200,field:value}
    with pytest.raises(ValueError):
        normalize_trade(row,60400,datetime(2026,10,7,10,9,tzinfo=VN))


def test_tickers_are_normalized_deduplicated_and_bounded():
    assert normalize_symbols(' fpt,HPG,FPT ') == ['FPT','HPG']
    with pytest.raises(ValueError):
        normalize_symbols(['FPT']*51)
    with pytest.raises(ValueError):
        normalize_symbols('')


@pytest.fixture
def index_source():
    calls = []
    state = {'time':0, 'error':None, 'symbol':'VNINDEX', 'summary_day':'2026/10/06', 'now':datetime(2026,10,7,10,9,tzinfo=VN)}
    def upstream(request):
        if request.url.path.endswith('/token'):
            return httpx.Response(200,json={'accessToken':'private-token','expiresAt':4102444800000})
        calls.append(request)
        if state['error'] == 'timeout':
            raise httpx.ReadTimeout('private upstream details')
        if state['error'] == 'rate':
            return httpx.Response(429,headers={'Retry-After':'30'},json={'msg':'private upstream details'})
        if request.url.path.endswith('/indexSummary'):
            return httpx.Response(200,json=[{'tradingDate':state['summary_day'],'indexValue':'1759.08',
                'indexChange':'5.88','indexChangePercentage':'0.34','totalTrade':'100','totalTradeValue':'1234'}])
        if request.url.params.get('timeFrame') == '1d':
            if request.url.params.get('pageIndex') != '1':
                return httpx.Response(200,json={'data':[]})
            return httpx.Response(200,json={'data':[{'symbol':'VNINDEX','tradingDate':'2026/10/06',
                'open':'1755','high':'1763','low':'1734','close':'1759.08','volume':'100'}]})
        return httpx.Response(200,json={'data':[{'symbol':state['symbol'],'tradingDate':'2026/10/07 10:08:32','close':'1747.11'}]})
    provider = SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='private-key',ssi_api_secret='private-secret'),
                                   transport=httpx.MockTransport(upstream),today=lambda:state['now'].date())
    live = SsiLiveMarket(provider,clock=lambda:state['now'],monotonic=lambda:state['time'])
    yield live,calls,state
    live.close();provider.close()


def test_index_today_date_source_timestamp_and_cache_are_independent_of_daily_bars(index_source):
    live,calls,state = index_source
    first = live.index()
    assert first['snapshot']['trading_date'] == '2026-10-07'
    assert first['snapshot']['updated_at'] == '2026-10-07T10:08:32+07:00'
    assert first['snapshot']['level'] == 1747.11
    assert first['snapshot']['change'] == pytest.approx(-11.97)
    assert first['snapshot']['total_volume'] is None # Do not mix previous-session aggregates.
    assert first['snapshot']['total_value'] is None
    assert first['session'] == 'active'
    count = len(calls)
    assert live.index() == first
    assert len(calls) == count
    state['time'] = 11
    live.index()
    assert len(calls) == count+1


@pytest.mark.parametrize('error',['timeout','rate'])
def test_failed_index_refresh_keeps_explicit_stale_snapshot_and_sanitized_errors(index_source,error):
    live,calls,state = index_source
    assert live.index()['status'] == 'fresh'
    state.update(time=11,error=error)
    result = live.index()
    assert result['status'] == 'stale'
    assert result['snapshot']['level'] == 1747.11
    assert 'private' not in str(result)


def test_unavailable_index_never_fabricates_zeros(index_source):
    live,calls,state = index_source
    state['error'] = 'timeout'
    assert live.index()['snapshot'] is None
    assert live.index()['status'] == 'unavailable'


def test_old_timestamp_cannot_confirm_an_active_trading_day(index_source):
    live,calls,state = index_source
    live.index()
    state['now'] = datetime(2026,10,8,10,0,tzinfo=VN)
    result=live.index()
    assert result['status']=='stale'
    assert result['session']=='unknown'


def test_equity_stream_cache_is_shared_by_symbol_and_bad_ticks_do_not_poison_it(index_source):
    live,calls,state=index_source
    # Demand is registered through the public read boundary; raw SSI events enter accept().
    first=live.read(['FPT','HPG','FPT'])
    assert set(first['items'])=={'FPT','HPG'}
    tick={'channel':'DATA','topic':'trade.FPT','data':{'s':'FPT','t':'2026/10/07 10:08:32','p':60300,'v':1200}}
    live.accept(tick)
    result=live.read(['FPT','HPG'])
    assert result['items']['FPT']['snapshot']['last_price']==60300
    assert result['items']['HPG']=={'status':'unavailable','snapshot':None}
    assert result['items']['FPT']['snapshot']['reference_price'] is None
    live.accept(dict(tick,data=dict(tick['data'],p='NaN')))
    assert live.read(['FPT'])['items']['FPT']==result['items']['FPT']
    live.accept(dict(tick,topic='trade.VNM',data=dict(tick['data'],s='VNM')))
    assert live.read(['VNM'])['items']['VNM']['snapshot'] is None
    state['now']=datetime(2026,10,7,10,12,tzinfo=VN)
    assert live.read(['FPT'])['items']['FPT']['status']=='stale'
    assert not calls  # Read cycles reuse stream state, with no per-cycle REST traffic.


def test_live_api_validates_equities_preserves_partial_availability_and_never_onboards(client,session,index_source):
    from main import app
    from src.models import Security,Stock
    from src.services.live_market import get_live_market
    live,_,_=index_source
    session.add(Security(symbol='FPT',exchange='HOSE',source='SSI:FastConnect',last_synced_at=datetime(2026,10,7,tzinfo=VN)))
    session.commit()
    app.dependency_overrides[get_live_market]=lambda:live
    response=client.get('/stocks/live?symbols=fpt,FPT,UNKNOWN')
    assert response.status_code==200
    assert set(response.json()['items'])=={'FPT','UNKNOWN'}
    assert response.json()['items']['UNKNOWN']['status']=='unavailable'
    assert session.get(Stock,'FPT') is None
    for raw in ['FPT/../','FPT,' ,','.join(['FPT']*51)]:
        assert client.get('/stocks/live',params={'symbols':raw}).status_code==422
    assert 'private' not in response.text


def test_reference_from_an_older_session_is_not_an_intraday_delta(index_source):
    live,_,state=index_source
    state['summary_day']='2026/10/05'
    result=live.index()
    assert result['snapshot']['level']==1747.11
    assert result['snapshot']['change'] is None
    assert result['snapshot']['change_percent'] is None


def test_mismatched_index_and_equity_identity_are_unavailable(index_source):
    live,_,state=index_source
    state['symbol']='HPG'
    assert live.index()['snapshot'] is None
    state['now']=datetime(2026,10,7,16,0,tzinfo=VN)
    assert live.read(['FPT'])['items']['FPT']['snapshot'] is None


def test_caller_release_does_not_remove_other_callers_overlapping_demand(index_source):
    live,_,_=index_source
    live.read(['FPT','HPG'],client_id='explore')
    live.read(['FPT'],client_id='detail')
    live.release('explore')
    tick={'channel':'DATA','topic':'trade.FPT','data':{'s':'FPT','t':'2026/10/07 10:08:32','p':60300}}
    live.accept(tick)
    live.accept(dict(tick,topic='trade.HPG',data=dict(tick['data'],s='HPG')))
    assert live.read(['FPT'],client_id='detail')['items']['FPT']['snapshot']['last_price']==60300
    assert live.read(['HPG'],client_id='new')['items']['HPG']['snapshot'] is None


def test_source_retry_after_is_respected_without_leaking_rate_error(index_source):
    live,calls,state=index_source
    live.index();state.update(time=11,error='rate')
    live.index();count=len(calls)
    state.update(time=25,error=None)
    assert live.index()['status']=='stale'
    assert len(calls)==count
    state['time']=42
    assert live.index()['status']=='fresh'


def test_old_morning_quote_is_not_promoted_to_fresh_after_close_or_during_break():
    morning=datetime(2026,10,7,10,0,tzinfo=VN)
    assert not source_fresh(morning,datetime(2026,10,7,16,0,tzinfo=VN),'closed')
    assert not source_fresh(morning,datetime(2026,10,7,12,0,tzinfo=VN),'break')
    closing=datetime(2026,10,7,14,45,tzinfo=VN)
    assert source_fresh(closing,datetime(2026,10,7,16,0,tzinfo=VN),'closed')
