import pandas as pd
import pytest
import json
import os
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.providers.vnstock.financial_packet import fetch_packet
from src.providers.vnstock.financial_statements import MAP, SECTIONS, content_hash
from src.services.financial_batch import acquire_batch
from src.services.personal_financials import personal_projection
from test_financial_engine import fixture as source_fixture
from src.providers.vnstock.financial_packet import packet_from_payloads


LABELS = {
    'isa3': ('Net sales', 'Doanh thu thuần'),
    'isa5': ('Gross profit', 'Lợi nhuận gộp'),
    'isa20': ('Net profit after tax', 'Lợi nhuận sau thuế'),
    'isb38': ('Total operating income', 'Tổng thu nhập hoạt động'),
    'isb27': ('Net interest income', 'Thu nhập lãi thuần'),
    'bsa53': ('Total assets', 'Tổng tài sản'),
    'bsa54': ('Liabilities', 'Nợ phải trả'),
    'bsa78': ("Owner's equity", 'Vốn chủ sở hữu'),
    'bsb104': ('Loans and advances to customers', 'Cho vay khách hàng'),
    'bsb113': ('Deposits from customers', 'Tiền gửi của khách hàng'),
    'cfa18': ('Net cash from operating activities', 'Lưu chuyển tiền thuần từ hoạt động kinh doanh'),
    'cfa26': ('Net cash from investing activities', 'Lưu chuyển tiền thuần từ hoạt động đầu tư'),
    'cfa34': ('Net cash from financing activities', 'Lưu chuyển tiền thuần từ hoạt động tài chính'),
}


def fake_sdk(company_type='CT', period_count=4):
    metadata = []
    for kind, fields in MAP.items():
        for field, (code, _) in fields.items():
            if code not in LABELS:
                continue
            en, vi = LABELS[code]
            metadata.append(dict(report_name=SECTIONS[kind], field_name=code, name=vi,
                en_name=en, parent='isa3' if code == 'isa5' else None))
    metadata_frame = pd.DataFrame(metadata)
    metadata_frame['report_name'] = metadata_frame['report_name'].astype(str)
    frames = {}
    for kind, fields in MAP.items():
        records = []
        for field, (code, _) in fields.items():
            if code not in LABELS:
                continue
            en, vi = LABELS[code]
            row = dict(item_id=code, item=vi, item_en=en)
            for index in range(period_count):
                row[f'{2026-index//4}-Q{4-index%4}'] = (index + 1) * 10
            for index in range(period_count):
                row[str(2025-index)] = (index + 1) * 100
            records.append(row)
        frames[kind] = pd.DataFrame(records)

    class Provider:
        base_url = 'https://example.test'
        com_type_code = company_type

        def _get_ratio_dict(self, *, format, show_log):
            assert format == 'dataframe' and show_log is False
            return metadata_frame

    class Finance:
        provider = Provider()

        def __init__(self):
            self.calls = []

        def _statement(self, kind, period, lang, dropna, show_log):
            self.calls.append((kind, period, lang, dropna, show_log))
            columns = ['item_id', 'item', 'item_en']
            columns += [c for c in frames[kind].columns if
                (isinstance(c, str) and ('-Q' in c if period == 'quarter' else c.isdigit()))]
            return frames[kind][columns]

        def income_statement(self, **kwargs): return self._statement('income', **kwargs)
        def balance_sheet(self, **kwargs): return self._statement('balance', **kwargs)
        def cash_flow(self, **kwargs): return self._statement('cash', **kwargs)

    instance = Finance()
    class SDK:
        @staticmethod
        def Finance(**kwargs):
            assert kwargs == dict(symbol='ABC', source='VCI', period='quarter', get_all=False, show_log=False)
            return instance

    return SDK, instance


def test_vci_packet_uses_sdk_finance_outputs_and_keeps_source_hierarchy_and_unknowns(monkeypatch):
    sdk, instance = fake_sdk()
    monkeypatch.setattr('src.providers.vnstock.financial_packet.version', lambda name: '4.0.2')
    packet = fetch_packet('abc', sdk)
    assert packet.ticker == 'ABC' and packet.source == 'vnstock:VCI' and packet.source_version == '4.0.2'
    assert packet.profile == 'non_financial'
    assert all(len(packet.reports[k].observations) == 8 for k in MAP)
    assert [call[1] for call in instance.calls] == ['quarter', 'year'] * 3
    quarter = next(o for o in packet.reports['income'].observations if o.period.endswith('-Q4'))
    assert quarter.fields['revenue'] == 10
    assert next(i for i in quarter.items if i.code == 'isa5').parent == 'isa3'
    assert quarter.source_context.original_currency is None
    assert quarter.source_context.original_unit is None
    assert quarter.source_context.period_start is None and quarter.source_context.period_end is None
    assert quarter.source_context.publication_time_qualified is False
    view = personal_projection(packet, frequency='quarterly', limit=4, authorization_reference='task:test')
    assert len(view['rows']) == 4
    assert view['rows'][-1]['revenue'] is not None


def test_vci_packet_keeps_successful_frequency_when_one_sdk_call_fails(monkeypatch):
    sdk, instance = fake_sdk()
    original = instance.balance_sheet
    def failing_balance(**kwargs):
        if kwargs['period'] == 'year':
            raise RuntimeError('source temporarily unavailable')
        return original(**kwargs)
    instance.balance_sheet = failing_balance
    monkeypatch.setattr('src.providers.vnstock.financial_packet.version', lambda name: '4.0.2')
    packet = fetch_packet('ABC', sdk)
    receipt = packet.reports['balance']
    assert receipt.status == 'healthy'
    assert len([o for o in receipt.observations if o.frequency == 'quarterly']) == 4
    assert not [o for o in receipt.observations if o.frequency == 'annual']
    assert all('sdk_annual_read_error:RuntimeError' in o.diagnostics for o in receipt.observations)


def test_vci_sdk_packet_uses_provider_reported_bank_profile(monkeypatch):
    sdk, _ = fake_sdk(company_type='NH')
    monkeypatch.setattr('src.providers.vnstock.financial_packet.version', lambda name: '4.0.2')
    result = fetch_packet('ABC', sdk)
    assert result.company_type == 'NH' and result.profile == 'bank'
    assert all(result.reports[name].status == 'healthy' for name in MAP)


def test_vci_sdk_adapter_rejects_more_than_the_installed_four_period_bound(monkeypatch):
    sdk, _ = fake_sdk(period_count=5)
    monkeypatch.setattr('src.providers.vnstock.financial_packet.version', lambda name: '4.0.2')
    packet = fetch_packet('ABC', sdk)
    assert all(receipt.status == 'error' and not receipt.observations for receipt in packet.reports.values())


def packet(ticker='ABC', quarters=4, annual=4, marker=1):
    metadata, reports = source_fixture()
    data = {kind: {'years': [], 'quarters': []} for kind in MAP}
    for kind, report in reports.items():
        data[kind]['years'] = [dict(row, ticker=ticker) for row in report['years'][-annual:]]
        data[kind]['quarters'] = [dict(row, ticker=ticker) for row in report['quarters'][-quarters:]]
    data['income']['quarters'][-1]['isa3'] = 30 + marker
    return packet_from_payloads(ticker, 'vnstock:VCI', 'CT', metadata, data,
        source_version='4.0.2', is_fixture=False)


def test_batch_add_skip_resume_and_isolate_ticker_failures(tmp_path):
    private = tmp_path / '.local'
    captures = private / 'captures'
    calls = []
    def fetch(ticker):
        calls.append(ticker)
        if ticker == 'BAD':
            raise RuntimeError('source unavailable')
        return packet(ticker)
    first = acquire_batch(captures, ['AAA', 'BAD', 'BBB'], fetch_packet=fetch, private_root=private)
    assert first['added'] == 2 and first['errors'] == {'BAD': 'RuntimeError'}
    assert calls == ['AAA', 'BAD', 'BBB']
    index = json.loads((captures / 'index.json').read_text(encoding='utf-8'))
    assert set(index['captures']) == {'AAA', 'BBB'}
    stored, _ = __import__('src.services.personal_financials', fromlist=['saved_packet']).saved_packet(captures, 'AAA')
    assert len(stored.reports['income'].observations) == 7
    resumed = acquire_batch(captures, ['AAA', 'BBB'], fetch_packet=lambda _: pytest.fail('existing ticker fetched'), private_root=private)
    assert resumed['skipped_existing'] == 2 and resumed['added'] == 0


def test_refresh_preserves_capture_revisions_and_does_not_shrink_history(tmp_path):
    private = tmp_path / '.local'; captures = private / 'captures'
    original = packet('AAA', quarters=8, annual=4)
    captures.mkdir(parents=True)
    body = (original.model_dump_json(indent=2) + '\n').encode('utf-8')
    digest = __import__('hashlib').sha256(body).hexdigest()
    name = f'AAA-vci-{digest}.json'
    (captures / name).write_bytes(body)
    (captures / 'index.json').write_text(json.dumps({'contract':'personal-saved-captures-v1',
        'captures':{'AAA':{'file':name,'sha256':digest,'format':'canonical-financial-packet-v1'}}}),encoding='utf-8')
    first_index = json.loads((captures / 'index.json').read_text(encoding='utf-8'))
    first_entry = first_index['captures']['AAA']
    result = acquire_batch(captures, ['AAA'], fetch_packet=lambda _: packet('AAA', quarters=4, annual=4, marker=2),
        refresh=True, private_root=private)
    assert result['results'][0]['status'] == 'refresh_deferred_shorter_history'
    after = json.loads((captures / 'index.json').read_text(encoding='utf-8'))
    assert after['captures']['AAA'] == first_entry
    short_capture = tmp_path / '.local-short' / 'captures'
    acquire_batch(short_capture, ['BBB'], fetch_packet=lambda _: packet('BBB'), private_root=tmp_path / '.local-short')
    changed = packet('BBB', marker=2)
    changed.reports['income'].content_sha256 = content_hash({'revision': 2})
    revised = acquire_batch(short_capture, ['BBB'], fetch_packet=lambda _: changed, refresh=True,
        private_root=tmp_path / '.local-short')
    assert revised['refreshed'] == 1
    final_index = json.loads((short_capture / 'index.json').read_text(encoding='utf-8'))
    previous_entry = final_index['capture_history']['BBB'][0]
    assert final_index['captures']['BBB'] != previous_entry
    assert (short_capture / previous_entry['file']).is_file()


@pytest.mark.parametrize('tickers', [[], ['ABC', 'ABC'], ['../BAD'], ['A'] * 16])
def test_batch_rejects_invalid_or_unbounded_ticker_lists(tmp_path, tickers):
    private = tmp_path / '.local'; captures = private / 'captures'
    with pytest.raises(ValueError):
        acquire_batch(captures, tickers, fetch_packet=lambda ticker: packet(ticker), private_root=private)


def test_batch_rejects_capture_destinations_outside_private_root(tmp_path):
    private = tmp_path / '.local'
    with pytest.raises(ValueError, match='private .local'):
        acquire_batch(tmp_path / 'public' / 'financials', ['ABC'], fetch_packet=lambda _: packet(), private_root=private)


def test_new_capture_remains_compatible_with_existing_private_financial_api(tmp_path):
    private = tmp_path / '.local'; captures = private / 'captures'
    acquire_batch(captures, ['ABC'], fetch_packet=lambda ticker: packet(ticker), private_root=private)
    app = FastAPI()
    from routers.personal_research import router
    app.include_router(router)
    env = dict(APP_ENV='development', WOOFI_PERSONAL_RESEARCH='1', WOOFI_PERSONAL_BIND='127.0.0.1',
        WOOFI_PERSONAL_CAPTURES=str(captures))
    with patch.dict(os.environ, env):
        client = TestClient(app, client=('127.0.0.1', 1234), base_url='http://127.0.0.1')
        response = client.get('/personal-research/financials/ABC?frequency=quarterly&limit=34&evidence=provider')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'private, no-store'
    body = response.json()
    assert body['source'] == 'vnstock:VCI' and len(body['rows']) == 4
    assert {'income', 'balance', 'cash'} <= set(body['statements'])
