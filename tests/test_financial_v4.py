"""Synthetic acceptance for period/vintage integrity and dated book value."""
import copy
import hashlib
import json
import pytest
from test_free_financial_sources import reviewed
from src.providers.reviewed_reports import report_packet
from src.providers.reviewed_history import history_packet
from src.services.personal_financials import personal_projection
from src.services.financial_intelligence import metric_unit


def history(tmp_path):
    original=reviewed(tmp_path)
    newer=copy.deepcopy(original)
    newer['source']='issuer:example:2025'
    older=copy.deepcopy(original)
    older['source']='issuer:example:2024'
    # Distinct original binary and period labels, including an overlapping 2024
    # revision. The history explicitly selects the whole 2024 from the newer PDF.
    (tmp_path/'old.pdf').write_bytes(b'%PDF-synthetic-older-vintage')
    older['document_file']='old.pdf'
    older['document_sha256']=hashlib.sha256((tmp_path/'old.pdf').read_bytes()).hexdigest()
    for a in older['amounts']:
        a['year']-=1
        a['period_end']=f"{a['year']}-12-31"
        if a['period_start']:a['period_start']=f"{a['year']}-01-01"
        a['column_periods']=['2024','2023']
        a['column_header']['text']='2024 VND 2023 VND'
    older['pages'][0]['text']=older['pages'][0]['text'].replace('2025 VND 2024 VND','2024 VND 2023 VND')
    older['pages'][0]['text_sha256']=hashlib.sha256(older['pages'][0]['text'].encode()).hexdigest()
    docs=[]
    for name,e in [('new.json',newer),('old.json',older)]:
        raw=json.dumps(e).encode();(tmp_path/name).write_bytes(raw)
        docs.append(dict(file=name,sha256=hashlib.sha256(raw).hexdigest()))
    return dict(contract='reviewed-report-history-v1',ticker='ABC',source='issuer:example:reviewed-history',
        review_reference='synthetic:whole-period-review',issuer_names=['Example issuer'],documents=docs,
        selected_periods={'2025':docs[0]['sha256'],'2024':docs[0]['sha256'],'2023':docs[1]['sha256']})


def test_history_preserves_lineage_and_blocks_cross_document_calculations(tmp_path):
    manifest=history(tmp_path)
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    packet=history_packet(manifest,tmp_path)
    view=personal_projection(packet,authorization_reference='synthetic:private')
    rows={r['period']:r for r in view['rows']}
    assert len(rows)==3 and rows['2023']['net_profit']==80
    assert rows['2025']['net_profit_growth_yoy']==.25
    assert rows['2024']['net_profit_growth_yoy'] is None and rows['2024']['roe'] is None
    from src.analytics.financial_engine import financial_engine
    refs=financial_engine(packet).rows[0]['calculations']['net_profit']['inputs']
    meta=refs[0]['source_context']['original_metadata']
    assert meta['original_document_source']=='issuer:example:2024'
    assert refs[0]['content_sha256']==meta['original_receipt_sha256']
    assert packet.reports['income'].source_url=='https://example.test/ir'
    assert before=={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    assert not view['verification']['periods'][0]['metrics']['net_profit']['dimensions']['POINT_IN_TIME_VERIFIED']


@pytest.mark.parametrize('mutation',[
    lambda e:e['selected_periods'].pop('2023'),
    lambda e:e['selected_periods'].update({'2023':'f'*64}),
    lambda e:e.update(ticker='XYZ'),
    lambda e:e.update(issuer_names=['Another issuer']),
    lambda e:e['documents'][0].update(file='../outside.json'),
])
def test_history_rejects_ambiguous_periods_and_unpinned_owners(tmp_path,mutation):
    manifest=history(tmp_path);mutation(manifest)
    with pytest.raises((ValueError,OSError)):history_packet(manifest,tmp_path)


def test_book_value_uses_same_date_ordinary_equity_and_actual_share_units(tmp_path):
    e=reviewed(tmp_path);page=e['pages'][0]
    for field,label,unit,value in [('ordinary_equity','Ordinary capital and reserves','VND',700),
            ('ordinary_shares','Number of ordinary shares','shares',100)]:
        row=f'{label} {value} {value}';page['text']+='\n'+row
        for year in (2025,2024):
            e['amounts'].append(dict(field=field,code='row:'+field,code_kind='reviewed_row_locator',label=label,
                year=year,raw_token=str(value),column_periods=['2025','2024'],column_values=[str(value)]*2,
                source_row=dict(page=1,text=row),column_header=dict(page=1,text='2025 VND 2024 VND'),
                unit_quote=dict(page=1,text='Number of ordinary shares' if unit=='shares' else 'VND'),
                unit=unit,period_start=None,period_end=f'{year}-12-31'))
    page['text_sha256']=hashlib.sha256(page['text'].encode()).hexdigest()
    packet,_=report_packet(e,tmp_path)
    result=personal_projection(packet,authorization_reference='synthetic:private')
    assert result['rows'][-1]['bvps']==7
    assert metric_unit('bvps')=='VND/share' and metric_unit('ordinary_shares')=='shares'
    assert next(m for m in result['fundamental_summary']['metrics'] if m['key']=='bvps')['value']==7
    assert all(m['value'] is None for m in result['fundamental_summary']['metrics'] if m['key'] in ('pe','pb','market_cap'))
    bad=copy.deepcopy(e);bad['amounts'][-1]['unit']='million VND'
    with pytest.raises(ValueError):report_packet(bad,tmp_path)


@pytest.mark.parametrize('shares',[0,-100])
def test_invalid_share_count_withholds_book_value_without_hiding_other_financials(tmp_path,shares):
    from src.analytics.financial_engine import financial_engine
    packet,_=report_packet(reviewed(tmp_path),tmp_path)
    obs=packet.reports['balance'].observations[-1]
    obs.fields.update(ordinary_equity=700,ordinary_shares=shares)
    result=financial_engine(packet)
    assert result.rows[-1]['bvps'] is None
    assert result.rows[-1]['net_profit']==100
    from src.analytics.financial_catalog import specialist_consistency
    assert not specialist_consistency(dict(field='ordinary_shares',value=shares))
