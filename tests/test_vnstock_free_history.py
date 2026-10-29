import sys
from types import SimpleNamespace
import pandas as pd
import pytest
from src.providers.vnstock.financial_packet import fetch_packet
from src.providers.vnstock.financial_statements import MAP, SECTIONS

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

@pytest.mark.parametrize('limit,count,healthy', [(4,4,True),(4,5,False),(8,8,True),(8,9,False),(None,5,False),(9,5,False),(True,5,False),('8',5,False)])
def test_history_respects_sdk_entitlement(monkeypatch,limit,count,healthy):
    monkeypatch.setitem(sys.modules,'vnai.beam.patching',SimpleNamespace(get_max_periods=lambda:limit))
    sdk,instance=fake_sdk(period_count=count)
    captured=fetch_packet('ABC',sdk)
    assert len(instance.calls)==6
    for receipt in captured.reports.values():
        assert (receipt.status=='healthy') is healthy
        assert len(receipt.observations)==(2*count if healthy else 0)

def test_policy_failure_is_guest_bounded(monkeypatch):
    def unavailable(): raise RuntimeError('offline')
    monkeypatch.setitem(sys.modules,'vnai.beam.patching',SimpleNamespace(get_max_periods=unavailable))
    sdk,_=fake_sdk(period_count=5)
    assert all(not r.observations for r in fetch_packet('ABC',sdk).reports.values())
