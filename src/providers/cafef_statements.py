"""Bounded saved CafeF annual summaries. No live fallback or provider SDK.

The separately reviewed thousand-VND feed convention is an inferred transport
scale, not original filing metadata. Gross sales is NOT canonical net revenue;
total liabilities is NOT interest-bearing debt. No ratios are imported.
"""
from datetime import datetime
import hashlib
import json
import math
import re
from src.providers.vnstock.financial_statements import MAP, content_hash
from src.schemas.financials import FinancialPacket, FinancialSourceContext, FinancialLine, StatementObservation, StatementReceipt

SOURCE = 'CafeF:annual-summary'
ENDPOINT = 'https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx'
FIELDS = {
 'income': {
  'gross_profit': ('LNGBHCCDV', r'^Lợi nhuận gộp về BH và CCDV$'),
  'net_profit': ('LNSTTNDN', r'^Lợi nhuận (KT )?sau thuế( TNDN)?$'),
  'profit_parent': ('NetIncome', r'^Lợi nhuận sau thuế của công ty mẹ$'),
 },
 'balance': {
  'total_assets': ('TotalAsset', r'^Tổng tài sản$'),
  'total_liabilities': ('TotalDebt', r'^Tổng nợ$'),
  'equity': ('TotalOwnerCapital', r'^Vốn chủ sở hữu$'),
  'current_assets': ('ShortTermFloatingCapital', r'^Tổng tài sản lưu động ngắn hạn$'),
  'current_liabilities': ('TotalShortTermDebt', r'^Nợ ngắn hạn$'),
 },
}


def cafef_packet(capture):
    if (capture.get('contract') != 'cafef-saved-annual-v1' or capture.get('source') != SOURCE
            or not re.fullmatch(r'[A-Z0-9]{1,20}', capture.get('ticker',''))
            or capture.get('company_type') not in ('CT','NH','CK','BH')):
        raise ValueError('Invalid CafeF capture owner/model')
    ticker = capture['ticker']
    profile = {'CT':'non_financial','NH':'bank','CK':'financial_other','BH':'financial_other'}[capture['company_type']]
    receipts = {}
    for kind in MAP:
        raw = capture.get('reports', {}).get(kind)
        if raw is None:
            receipts[kind] = StatementReceipt(statement=kind, status='unavailable',
                observed_at=datetime.fromisoformat(capture['observed_at']), source_url=ENDPOINT)
            continue
        observed = datetime.fromisoformat(raw['observed_at'])
        params = raw['params']
        if (kind not in FIELDS or raw.get('url') != ENDPOINT or observed.tzinfo is None
                or raw.get('status') != 200 or params.get('Symbol') != ticker or type(params.get('Type')) is not int
                or params.get('Type') != {'income':1,'balance':2}[kind]
                or params.get('ReportType') != 'NAM' or type(params.get('TotalRow')) is not int or not 1 <= params.get('TotalRow',0) <= 20):
            raise ValueError('Invalid CafeF receipt identity')
        # Exact saved HTTP body, not a reserialized object hash.
        body = raw['body']
        if not isinstance(body,str) or len(body.encode()) > 1_000_000 or hashlib.sha256(body.encode()).hexdigest() != raw['body_sha256']:
            raise ValueError('CafeF response hash mismatch')
        payload = json.loads(body)
        if payload.get('Success') is not True or not isinstance(payload.get('Data'),dict):
            raise ValueError('CafeF report unavailable')
        rows = payload['Data'].get('Value')
        if not isinstance(rows,list) or len(rows) > 20:
            raise ValueError('CafeF collection exceeds bound')
        observations, seen = [], set()
        for row in rows:
            year = row.get('Year')
            if (type(year) is not int or not 1900 <= year <= 2200 or type(row.get('Quater')) is not int or row.get('Quater') not in (0,5)
                    or row.get('Time') != str(year) or row.get('ReportType') != 'HK' or year in seen
                    or not isinstance(row.get('Value'),list) or len(row['Value']) > 100):
                raise ValueError('CafeF period ownership invalid')
            seen.add(year)
            indexed = {}
            for line in row['Value']:
                if not isinstance(line,dict) or not isinstance(line.get('Code'),str) or line['Code'] in indexed:
                    raise ValueError('CafeF ambiguous line identity')
                indexed[line['Code']] = line
            fields, codes, items, diagnostics = {f:None for f in MAP[kind]}, {}, [], []
            for field,(code,pattern) in FIELDS[kind].items():
                line = indexed.get(code)
                if not line or field in ('gross_profit','current_assets','current_liabilities') and profile != 'non_financial':
                    continue
                label = line.get('Name')
                value = line.get('Value')
                if value is not None and (type(value) not in (int,float) or not math.isfinite(value)):
                    raise ValueError('CafeF amount is not a finite JSON number')
                valid = isinstance(label,str) and bool(re.fullmatch(pattern,label))
                normalized = value * 1000 if value is not None else None
                if normalized is not None and (not math.isfinite(normalized) or abs(normalized) > 2**53-1):
                    raise ValueError('CafeF amount exceeds safe precision')
                fields[field] = normalized if valid else None
                codes[field] = code
                if not valid: diagnostics.append('conflicted_metadata:'+code)
                items.append(FinancialLine(code=code, name_en=field.replace('_',' '),
                    name_vi=str(label or code), value=fields[field], raw_value=value, unit='VND',
                    semantic_status='reported' if valid else 'conflicted',
                    source_labels=[dict(name=str(label or code))]))
            ctx = FinancialSourceContext(fiscal_year=year, data_confidence='SOURCE_REPORTED',
                record_sha256=content_hash(row), amount_multiplier=1000,
                unit_evidence='audited_cafef_adapter_contract',
                original_metadata=dict(reported_audit_description=row.get('Conten'),
                    transport_scale_origin='inferred_reviewed_contract_not_original_metadata',
                    transport_scale_reference='research/PROVIDER_METADATA_AUDIT.md#cafef',
                    requested_period='NAM', reported_period=row['ReportType']))
            observations.append(StatementObservation(ticker=ticker, source=SOURCE, statement=kind,
                period=str(year), frequency='annual', basis='point_in_time' if kind=='balance' else 'annual',
                fields=fields, field_codes=codes, items=items, diagnostics=diagnostics, source_context=ctx))
        receipts[kind] = StatementReceipt(statement=kind, status='healthy' if observations else 'unavailable',
            observations=sorted(observations,key=lambda o:o.period), observed_at=observed,
            content_sha256=raw['body_sha256'], source_url=ENDPOINT)
    return FinancialPacket(ticker=ticker, source=SOURCE, source_version='cafef-saved-annual-v1',
        company_type=capture['company_type'], profile=profile,
        metadata_sha256=content_hash(FIELDS), reports=receipts)
