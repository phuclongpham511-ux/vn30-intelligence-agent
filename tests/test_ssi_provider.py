from datetime import date
import httpx
import pytest
from src.providers.ssi import SsiMarketDataProvider
from src.config.settings import Settings
from src.providers.base import ProviderError, ProviderNotReadyError
from src.providers.ssi import vietnam_today


def row(day='2024/09/20', **changes):
    return {'symbol':'XYZ', 'tradingDate':day, 'open':'19750', 'high':'20100',
            'low':'19650', 'close':'19650', 'volume':'15048900', **changes}


@pytest.fixture
def make_provider():
    providers = []
    def make(respond):
        def handler(request):
            if request.url.path.endswith('/token'):
                return httpx.Response(200, json={'accessToken':'private-token', 'expiresAt':4102444800000})
            return respond(request)
        provider = SsiMarketDataProvider(
            Settings(_env_file=None, ssi_api_key='private-key', ssi_api_secret='private-secret'),
            transport=httpx.MockTransport(handler), today=lambda:date(2024,9,21))
        providers.append(provider)
        return provider
    yield make
    for provider in providers:
        provider.close()


@pytest.mark.parametrize('change', [
    {'open':None}, {'high':None}, {'low':None}, {'close':None}, {'volume':None},
    {'open':'NaN'}, {'high':'inf'}, {'volume':'-1'}, {'close':'0'},
    {'high':'19500'}, {'low':'19800'}, {'close':'oops'}, {'volume':False},
    {'tradingDate':'not-a-date'},
])
def test_invalid_required_data_fails_without_sdk_zero_coercion(make_provider, change):
    provider = make_provider(lambda request:httpx.Response(200, json={'data':[row(**change)]}))
    with pytest.raises(ProviderError, match='temporarily unavailable'):
        provider.get_history('XYZ',date(2024,9,19),date(2024,9,21))


def test_pagination_clipping_sorting_duplicates_and_cache(make_provider):
    requests = []
    pages = {1:[row('2024/09/20'),row('2024/09/19'),row('2024/09/18')],
             2:[row('2024/09/19'),row('2024/09/17')],3:[]}
    def respond(request):
        requests.append(dict(request.url.params))
        return httpx.Response(200, json={'data':pages[int(request.url.params['pageIndex'])]})
    provider=make_provider(respond)
    bars=provider.get_history('xyz',date(2024,9,18),date(2024,9,21))
    assert [b.date for b in bars]==[date(2024,9,18),date(2024,9,19),date(2024,9,20)]
    assert len(requests)==3
    assert all(r['from']=='2024/09/18 00:00:00' and r['to']=='2024/09/20 23:59:59' for r in requests)
    bars[0].close=1
    assert provider.get_history('XYZ',date(2024,9,18),date(2024,9,21))[0].close==19650
    assert len(requests)==3


def test_fresh_history_bypasses_five_minute_cache(make_provider):
    requests=[]
    def respond(request):
        requests.append(dict(request.url.params))
        return httpx.Response(200,json={'data':[row()] if request.url.params['pageIndex']=='1' else []})
    provider=make_provider(respond)
    start,end=date(2024,9,19),date(2024,9,20)
    assert len(provider.get_history('XYZ',start,end))==1
    assert len(provider.get_history('XYZ',start,end))==1
    assert len(requests)==2
    assert len(provider.get_history_fresh('XYZ',start,end))==1
    assert len(requests)==4


def test_conflicting_duplicate_rejected(make_provider):
    provider=make_provider(lambda request:httpx.Response(200,json={'data':[row(),row(close='19700')]}))
    with pytest.raises(ProviderError):
        provider.get_history('XYZ',date(2024,9,19),date(2024,9,21))


def test_security_normalization_invalid_and_hourly_cache(make_provider):
    calls=[]
    def respond(request):
        calls.append(request.url.params['symbol'])
        data=[{'symbol':'XYZ','board':'HOSE','symbolNameEn':'Example Company'}] if calls[-1]=='XYZ' else []
        return httpx.Response(200,json=data)
    provider=make_provider(respond)
    assert provider.validate_symbol(' xyz ')
    assert provider.company_name('XYZ')=='Example Company'
    assert not provider.validate_symbol('NOSUCH')
    assert not provider.validate_symbol('!')
    assert calls==['XYZ','NOSUCH']


def test_equity_universe_uses_type_not_ticker_shape_and_never_fetches_prices(make_provider):
    calls = []
    def respond(request):
        calls.append(dict(request.url.params))
        board = request.url.params['board']
        stock = dict(symbol=' xy1 ' if board == 'HOSE' else board, board=board,
            stockType='Stock', symbolNameEn='Example issuer', symbolNameVi='Issuer')
        return httpx.Response(200, json=[stock, stock,
            dict(symbol='ABC', board=board, stockType='ETF Product'),
            dict(symbol='UNKNOWN', board=board)])
    snapshot = make_provider(respond).get_security_universe()
    assert snapshot.raw_count == 12
    assert [row.symbol for row in snapshot.securities] == ['HNX', 'UPCOM', 'XY1']
    assert snapshot.exclusions == {'ETF Product': 3, 'unknown': 3}
    assert snapshot.duplicate_count == 3
    assert snapshot.securities[-1].exchange == 'HOSE'
    assert snapshot.securities[-1].display_name_en == 'Example issuer'
    assert calls == [{'board':'HOSE'}, {'board':'HNX'}, {'board':'UPCOM'}]


@pytest.mark.parametrize('payload', [[], {}, [None], [{'symbol':'ABC','board':'HOSE','stockType':'Stock'}, {'symbol':'ABC','board':'HOSE','stockType':'Stock','symbolNameEn':'Conflicting'}]])
def test_security_master_fails_closed_on_empty_malformed_or_conflicting_data(make_provider, payload):
    with pytest.raises(ProviderError):
        make_provider(lambda request: httpx.Response(200, json=payload)).get_security_universe()


def test_security_master_upstream_failure_is_sanitized(make_provider):
    with pytest.raises(ProviderError, match='temporarily unavailable'):
        make_provider(lambda request: httpx.Response(500, text='private-secret')).get_security_universe()


@pytest.mark.parametrize('status',[401,429,500])
def test_upstream_failures_sanitized(make_provider, caplog, status):
    provider=make_provider(lambda request:httpx.Response(status,json={'message':'private-secret private-token'}))
    with caplog.at_level('DEBUG'), pytest.raises(ProviderError) as error:
        provider.validate_symbol('XYZ')
    for secret in ['private-key','private-secret','private-token','Authorization']:
        assert secret not in str(error.value)+caplog.text


def test_timeout_sanitized(make_provider, caplog):
    def respond(request):
        raise httpx.ConnectError('private-secret',request=request)
    provider=make_provider(respond)
    with pytest.raises(ProviderError) as error:
        provider.validate_symbol('XYZ')
    assert 'private-secret' not in str(error.value)+caplog.text


@pytest.mark.parametrize('payload',[None,{}, {'data':None},{'data':[{}]}, {'code':500,'data':[]}])
def test_malformed_payload_sanitized(make_provider,payload):
    provider=make_provider(lambda request:httpx.Response(200,json=payload))
    with pytest.raises(ProviderError):
        provider.get_history('XYZ',date(2024,9,19),date(2024,9,21))


def test_vietnam_day_uses_aware_timezone(monkeypatch):
    from datetime import datetime, timezone
    class Clock:
        @staticmethod
        def now(zone):
            return datetime(2024,9,20,18,tzinfo=timezone.utc).astimezone(zone)
    monkeypatch.setattr('src.providers.ssi.datetime',Clock)
    assert vietnam_today()==date(2024,9,21)


def test_configuration_selection_without_fallback(monkeypatch):
    from src.services.stocks import get_market_provider
    from src.providers.vnstock import VnstockMarketDataProvider
    for selected, expected in [('ssi',SsiMarketDataProvider),('vnstock',VnstockMarketDataProvider)]:
        monkeypatch.setattr('src.services.stocks.get_settings',lambda:Settings(_env_file=None,market_data_provider=selected))
        get_market_provider.cache_clear()
        assert isinstance(get_market_provider(),expected)
    monkeypatch.setattr('src.services.stocks.get_settings',lambda:Settings(_env_file=None,market_data_provider='invalid'))
    get_market_provider.cache_clear()
    with pytest.raises(ProviderNotReadyError):
        get_market_provider()
    get_market_provider.cache_clear()
    provider=SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='',ssi_api_secret=''))
    with pytest.raises(ProviderNotReadyError):
        provider.get_history('XYZ',date(2024,9,19),date(2024,9,21))


def test_latest_excludes_current_session_and_keeps_real_zero_volume(make_provider):
    def respond(request):
        return httpx.Response(200,json={'data':[row('2024/09/21'),row(volume='0')]
            if request.url.params['pageIndex']=='1' else []})
    provider=make_provider(respond)
    latest=provider.get_latest('XYZ')
    assert latest.date==date(2024,9,20) and latest.volume==0


def test_pagination_failure_never_returns_partial_result(make_provider):
    def respond(request):
        if request.url.params['pageIndex']=='1':
            return httpx.Response(200,json={'data':[row()]})
        return httpx.Response(500,json={'message':'upstream'})
    provider=make_provider(respond)
    with pytest.raises(ProviderError):
        provider.get_history('XYZ',date(2024,9,19),date(2024,9,21))


def test_pagination_safety_bound(make_provider,monkeypatch):
    monkeypatch.setattr('src.providers.ssi.MAX_PAGES',3)
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(200,json={'data':[row()]})
    with pytest.raises(ProviderError):
        make_provider(respond).get_history('XYZ',date(2024,9,19),date(2024,9,21))
    assert len(calls)==3


def test_ssi_no_content_code_means_no_security_and_finished_history(make_provider):
    provider=make_provider(lambda request:httpx.Response(200,json={'code':204,'msg':'No Content'}))
    assert not provider.validate_symbol('NOSUCH')
    assert provider.get_latest('XYZ') is None


def test_timeout_retry_is_bounded_and_safe(make_provider, caplog):
    calls=[]
    def respond(request):
        calls.append(request)
        raise httpx.ReadTimeout('private-secret',request=request)
    with pytest.raises(ProviderError) as error:
        make_provider(respond).validate_symbol('XYZ')
    assert len(calls)==2
    assert 'private-secret' not in str(error.value)+caplog.text


def test_expired_access_token_reauthenticates_safely():
    auth_calls=[]
    def respond(request):
        if request.url.path.endswith('/token'):
            auth_calls.append(request)
            return httpx.Response(200,json={'accessToken':'private-token',
                'expiresAt':1 if len(auth_calls)==1 else 4102444800000})
        return httpx.Response(200,json={'code':204,'msg':'No Content'})
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='private-key',ssi_api_secret='private-secret'),
        transport=httpx.MockTransport(respond),today=lambda:date(2024,9,21)) as provider:
        assert not provider.validate_symbol('AAA')
        assert not provider.validate_symbol('BBB')
    assert len(auth_calls)==2


def test_authentication_failure_never_leaks_payload(caplog):
    def respond(request):
        return httpx.Response(401,json={'message':'private-secret private-token'})
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='private-key',ssi_api_secret='private-secret'),
        transport=httpx.MockTransport(respond)) as provider:
        with caplog.at_level('DEBUG'),pytest.raises(ProviderError) as error:
            provider.validate_symbol('XYZ')
        assert all(value not in str(error.value)+caplog.text for value in
                   ['private-key','private-secret','private-token','Authorization'])


def test_expired_token_refreshes_without_reauthenticating():
    paths=[]
    def respond(request):
        paths.append(request.url.path)
        if request.url.path.endswith('/token'):
            return httpx.Response(200,json={'accessToken':'private-token','expiresAt':1,'refreshToken':'private-refresh'})
        if request.url.path.endswith('/refresh'):
            return httpx.Response(200,json={'accessToken':'private-new-token','expiresAt':4102444800000})
        return httpx.Response(200,json={'code':204,'msg':'No Content'})
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='private-key',ssi_api_secret='private-secret'),
        transport=httpx.MockTransport(respond)) as provider:
        assert not provider.validate_symbol('AAA')
        assert not provider.validate_symbol('BBB')
    assert sum(path.endswith('/token') for path in paths)==1
    assert sum(path.endswith('/refresh') for path in paths)==1


def test_ssi_provider_at_existing_api_seam(client, make_provider):
    from datetime import timedelta
    from main import app
    from src.services.stocks import get_market_provider
    from src.services.data import get_fundamental_provider
    from src.schemas.data import FundamentalRecord
    def respond(request):
        if 'securities' in request.url.path.lower():
            return httpx.Response(200,json=[{'symbol':'XYZ','board':'HOSE','symbolNameEn':'Example Company'}])
        day=(vietnam_today()-timedelta(days=1)).strftime('%Y/%m/%d')
        return httpx.Response(200,json={'data':[row(day)] if request.url.params['pageIndex']=='1' else []})
    class Financial:
        source='vnstock:VCI'
        def get_financials(self,symbol):
            return [FundamentalRecord(ticker=symbol,period='2025',revenue=100,net_profit=20,source=self.source)]
    provider=make_provider(respond)
    provider._today=vietnam_today
    app.dependency_overrides[get_market_provider]=lambda:provider
    app.dependency_overrides[get_fundamental_provider]=Financial
    assert client.post('/stocks/validate',json={'ticker':' xyz '}).json()['valid'] is True
    assert client.post('/stocks',json={'ticker':'xyz'}).status_code==201
    for endpoint in ['history','market','technical-history','overview']:
        result=client.get('/stocks/XYZ/'+endpoint)
        assert result.status_code==200
        body=result.json()
        if endpoint=='overview':
            assert body['market']['source']=='SSI:FastConnect'
            assert body['fundamentals']['source']=='vnstock:VCI'
        elif isinstance(body,list):
            assert body[0]['source']=='SSI:FastConnect'
        else:
            assert body['source']=='SSI:FastConnect'


def test_ssi_missing_credentials_public_api_is_safe(client):
    from main import app
    from src.services.stocks import get_market_provider
    app.dependency_overrides[get_market_provider]=lambda:SsiMarketDataProvider(
        Settings(_env_file=None,ssi_api_key='',ssi_api_secret=''))
    result=client.post('/stocks/validate',json={'ticker':'XYZ'})
    assert result.status_code==200 and result.json()['valid'] is None
    assert 'not configured' in result.json()['message']
    result=client.post('/stocks',json={'ticker':'XYZ'})
    assert result.status_code==502 and 'secret' not in result.text


def test_raw_prices_remain_vnd_and_today_is_excluded():
    def respond(request):
        if request.url.path.endswith('/token'):
            return httpx.Response(200, json={'accessToken':'test-token','expiresAt':4102444800000})
        if request.url.params.get('pageIndex') != '1':
            return httpx.Response(200, json={'data':[]})
        return httpx.Response(200, json={'data':[
            {'symbol':'XYZ','tradingDate':'2024/09/21','open':'19750','high':'20100','low':'19650','close':'19650','volume':'100'},
            {'symbol':'XYZ','tradingDate':'2024/09/20','open':'19750','high':'20100','low':'19650','close':'19650','volume':'15048900'},
        ]})
    transport=httpx.MockTransport(respond)
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='test-key',ssi_api_secret='test-secret'),
                               transport=transport,today=lambda:date(2024,9,21)) as provider:
        bars=provider.get_history(' xyz ',date(2024,9,19),date(2024,9,21))
        assert [(b.date,b.close,b.volume,b.source) for b in bars]==[
            (date(2024,9,20),19650,15048900,'SSI:FastConnect')]


def test_index_groups_and_summary_preserve_raw_numbers_without_zero_fallback(make_provider):
    def respond(request):
        if request.url.path.endswith('/indexList'):
            return httpx.Response(200,json=[{'index':'VN30','board':'HOSE'},{'index':'VN100','board':'HOSE'},{'index':'HNX30','board':'HNX'}])
        if request.url.path.endswith('/securitiesByBoard'):
            return httpx.Response(200,json=[{'symbol':'XYZ','board':'HNX' if request.url.params['index']=='HNX30' else 'HOSE','stockType':'Stock'}])
        return httpx.Response(200,json=[{'tradingDate':'2024/09/20','indexValue':'1200.5','indexChange':'-10','indexChangePercentage':'-0.83'}])
    provider=make_provider(respond)
    assert provider.get_index_memberships()['VN30']==['XYZ']
    summary=provider.get_index_snapshot()
    assert summary['level']==1200.5 and summary['change']==-10 and summary['change_percent']==-0.83
    missing=make_provider(lambda _:httpx.Response(200,json=[{'tradingDate':'2024/09/20','indexValue':'1200.5','indexChange':None,'indexChangePercentage':None}]))
    assert missing.get_index_snapshot()['change'] is None
    invalid=make_provider(lambda _:httpx.Response(200,json=[{'tradingDate':'2024/09/20','indexValue':None}]))
    with pytest.raises(ProviderError): invalid.get_index_snapshot()


def test_index_summary_totals_are_nullable_real_numbers(make_provider):
    provider=make_provider(lambda _:httpx.Response(200,json=[{'tradingDate':'2024/09/20','indexValue':'1200','totalTrade':'791551098','totalTradeValue':'18715110854170'}]))
    row=provider.get_index_snapshot()
    assert (row['total_volume'],row['total_value'],row['trading_date'])==(791551098,18715110854170,'2024-09-20')
    missing=make_provider(lambda _:httpx.Response(200,json=[{'tradingDate':'2024/09/20','indexValue':'1200','totalTrade':None}])).get_index_snapshot()
    assert missing['total_volume'] is None and missing['total_value'] is None


def test_index_detail_uses_public_daily_history_without_onboarding(client):
    from main import app
    from src.services.stocks import get_market_provider
    calls=[]
    class Provider:
        def get_history(self,symbol,start,end):
            calls.append((symbol,start,end));return []
    app.dependency_overrides[get_market_provider]=Provider
    response=client.get('/stocks/index-history?start=2026-09-01&end=2026-10-01')
    assert response.status_code==200 and response.json()==[]
    assert calls==[('VNINDEX',date(2026,9,1),date(2026,10,1))]
