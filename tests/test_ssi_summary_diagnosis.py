"""Offline boundary checks for the October 20 No Content investigation.

Mock HTTP only. The saved ACB record is historical evidence, not live acceptance.
These tests do not assert why the provider returned business code 204.
"""
import copy
import json
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from ssi_sdk.constant import EP_DATA_SECURITIES_SUMMARY
from ssi_sdk.exceptions import ValidationError
from ssi_sdk.services.market_data import MarketDataService

from src.config.settings import Settings
from src.providers.ssi import SsiMarketDataProvider
from src.services.market_summary import compare_provisional_snapshots, normalize_summary_pair

SAVED = json.loads((Path(__file__).parent / 'fixtures/ssi-summary-acb-20261016.json').read_text(encoding='utf8'))
NO_CONTENT = {'code': 204, 'msg': 'No Content'}


@pytest.mark.parametrize('payload', [NO_CONTENT, {'data': [SAVED['record']]},
                                   {'code': 400, 'msg': 'Invalid request'}, {'data': None}])
def test_raw_adapter_preserves_business_envelope_without_promoting_it(payload):
    calls = []

    def respond(request):
        calls.append(request.url.path)
        if request.url.path.endswith('/token'):
            return httpx.Response(200, json={'accessToken': 'offline-test-token', 'expiresAt': 4102444800000})
        assert request.method == 'GET'
        assert dict(request.url.params) == {'symbol': 'ACB', 'from': '2026/10/20', 'to': '2026/10/20', 'pageIndex': '1', 'pageSize': '2'}
        return httpx.Response(200, json=copy.deepcopy(payload))

    with SsiMarketDataProvider(Settings(_env_file=None, database_url='sqlite://',
            ssi_api_key='offline-test-key', ssi_api_secret='offline-test-secret'),
            transport=httpx.MockTransport(respond)) as provider:
        actual = provider._request(EP_DATA_SECURITIES_SUMMARY,
            {'symbol': 'ACB', 'from': '2026/10/20', 'to': '2026/10/20', 'pageIndex': 1, 'pageSize': 2})
        assert actual == payload  # Includes code/msg, missing data, nulls and strings.
        if payload.get('data'):
            normalized = normalize_summary_pair(actual['data'][0],
                retrieved_at=SAVED['received_at'], expected_symbol='ACB')
            assert normalized['volume']['raw_value'] == '5160300'
            assert normalized['value']['raw_value'] == '106488260000'
            assert normalized['source_observed_at'] is None
            assert normalized['live_display_eligible'] is False
    assert calls == ['/api/v3/auth/token', EP_DATA_SECURITIES_SUMMARY]


def test_sdk_current_and_historical_methods_share_endpoint_and_date_contract():
    rest = Mock()
    rest.get.return_value = copy.deepcopy(NO_CONTENT)
    service = MarketDataService(rest)
    with patch('ssi_sdk.services.market_data.today_date_str', return_value='2026/10/20'):
        assert service.get_securities_summary('ACB') == []
    current = rest.get.call_args
    assert service.get_securities_summary_historical('ACB', '2026/10/20', '2026/10/20') == []
    assert rest.get.call_args == current
    assert current.args == (EP_DATA_SECURITIES_SUMMARY,)
    params = current.kwargs['params']
    assert {k: params[k] for k in ('symbol', 'from', 'to')} == {
        'symbol': 'ACB', 'from': '2026/10/20', 'to': '2026/10/20'}
    # SDK defaults differ from the diagnostic's bounded pageSize=2, not its date format.
    assert params['pageIndex'] == 1


@pytest.mark.parametrize('args', [('', '2026/10/20', '2026/10/20'),
                                  ('ACB', '', '2026/10/20'), ('ACB', '2026/10/20', '')])
def test_sdk_rejects_missing_required_strings_without_transport(args):
    rest = Mock()
    with pytest.raises(ValidationError):
        MarketDataService(rest).get_securities_summary_historical(*args)
    rest.get.assert_not_called()


@pytest.mark.parametrize('raw', [NO_CONTENT, {'data': []}, {'data': None}])
def test_response_envelopes_cannot_be_normalized_as_a_summary_record(raw):
    with pytest.raises(ValueError):
        normalize_summary_pair(raw, retrieved_at=SAVED['received_at'], expected_symbol='ACB')


def test_missing_snapshot_cannot_be_compared_as_zero_or_unchanged():
    with pytest.raises(ValueError):
        compare_provisional_snapshots(None, None, now='2026-10-20T09:37:23+07:00')
