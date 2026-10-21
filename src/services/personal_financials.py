"""Offline personal projection; never grants public rights or invents basis.

Only reviewed adapter fields enter charts. Unknown-basis observations may be
displayed individually; derived ratios, growth and compositions still require
the ordinary qualification gates. Saved captures are immutable and hash pinned.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import math

from src.analytics.financial_engine import financial_engine
from src.providers.vnstock.financial_packet import metadata_rows, packet_from_payloads
from src.providers.vnstock.financial_statements import MAP, NON_FINANCIAL_ONLY, BANK_ONLY, statement_line_unit
from src.schemas.financials import FinancialPacket
from src.services.financial_presentation import display_financial_response

CONFIDENCES = ('OFFICIAL_VERIFIED', 'RECONCILED', 'SOURCE_REPORTED', 'UNVERIFIED', 'INVALID')


def saved_packet(directory, ticker, *, collection='captures'):
    """Read a pinned source receipt only. No SDK, cache fallback or acquisition."""
    if not re.fullmatch(r'[A-Z0-9]{1,20}', ticker):
        raise ValueError('Invalid ticker')
    root = Path(directory).resolve(strict=True)
    if (root / 'index.json').stat().st_size > 2_000_000:
        raise ValueError('Saved capture index exceeds bound')
    index = json.loads((root / 'index.json').read_text(encoding='utf-8'))
    if index.get('contract') != 'personal-saved-captures-v1' or not isinstance(index.get('captures'), dict):
        raise ValueError('Invalid saved capture index')
    if collection not in ('captures', 'reviewed_reports'):
        raise ValueError('Unknown saved evidence collection')
    item = index.get(collection, {}).get(ticker)
    if not item:
        raise FileNotFoundError('Saved research coverage unavailable')
    path = (root / item['file']).resolve(strict=True)
    canonical = item.get('format') == 'canonical-financial-packet-v1'
    if item.get('format') not in (None, 'vci-raw-capture-v1', 'canonical-financial-packet-v1', 'reviewed-report-v2', 'reviewed-report-history-v1', 'cafef-saved-annual-v1'):
        raise ValueError('Unknown saved capture format')
    if not path.is_relative_to(root) or path.suffix != '.json' or path.stat().st_size > (32_000_000 if canonical else 10_000_000):
        raise ValueError('Invalid capture path')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError('Saved capture digest mismatch')
    if item.get('format') == 'reviewed-report-history-v1':
        from src.providers.reviewed_history import history_packet
        packet=history_packet(json.loads(data),root)
        if packet.ticker!=ticker:raise ValueError('Wrong history owner')
        return packet,item['sha256']
    if item.get('format') == 'reviewed-report-v2':
        from src.providers.reviewed_reports import report_packet
        packet, _ = report_packet(json.loads(data), root)
        if packet.ticker != ticker:
            raise ValueError('Wrong reviewed report owner')
        return packet, item['sha256']
    if item.get('format') == 'cafef-saved-annual-v1':
        from src.providers.cafef_statements import cafef_packet
        packet = cafef_packet(json.loads(data))
        if packet.ticker != ticker:
            raise ValueError('Wrong CafeF capture owner')
        return packet, item['sha256']
    if canonical:
        packet = validated_canonical_packet(data)
        if packet.ticker != ticker:
            raise ValueError('Wrong canonical capture owner')
        return packet, item['sha256']
    raw = json.loads(data)
    if raw['ticker'] != ticker or raw['source'] != 'vnstock:VCI' or raw.get('capture_kind') != 'LIVE_EXISTING_SDK_READ':
        raise ValueError('Invalid saved research identity')
    names = {'income': 'income_statement', 'balance': 'balance_sheet', 'cash': 'cash_flow'}
    reads = {kind: raw[name]['reads'][0] for kind, name in names.items()}
    packet = packet_from_payloads(ticker, raw['source'], raw['company_type'],
        metadata_rows(raw['metadata']['reads'][0]['data']),
        {kind: r['data'] for kind, r in reads.items()}, source_version=raw['sdk_version'],
        observed_at={kind: datetime.fromisoformat(r['observed_at']) for kind, r in reads.items()},
        urls={kind: r['url'] + '?section=' + r['params']['section'] for kind, r in reads.items()})
    return packet, item['sha256']


def saved_research_packet(directory, ticker, *, frequency='annual', evidence='preferred'):
    """Select a whole source packet, never splice provider and filing periods.

    Reviewed annual reports take priority only in annual mode. The complete
    original provider history remains selectable, and supplies quarterly/TTM.
    """
    if frequency not in ('annual', 'quarterly', 'ttm') or evidence not in ('preferred', 'provider'):
        raise ValueError('Invalid research evidence selection')
    if evidence == 'preferred' and frequency == 'annual':
        path = Path(directory) / 'index.json'
        if path.stat().st_size > 2_000_000:
            raise ValueError('Saved capture index exceeds bound')
        index = json.loads(path.read_text(encoding='utf-8'))
        if ticker in index.get('reviewed_reports', {}):
            return saved_packet(directory, ticker, collection='reviewed_reports')
    return saved_packet(directory, ticker)


def validated_canonical_packet(data):
    """Validate an immutable saved output of the existing VCI adapter.

    This is not original-transport verification: preserve that limitation.
    Recheck mapped fields against source lines and never accept a rights grant
    or invented fiscal metadata from this private canonical capture format.
    """
    if len(data) > 32_000_000:
        raise ValueError('Canonical packet exceeds bound')
    packet = FinancialPacket.model_validate_json(data, strict=True)
    if (packet.is_fixture or packet.source != 'vnstock:VCI'
            or set(packet.reports) != set(MAP)
            or not re.fullmatch(r'[A-Z0-9]{1,20}', packet.ticker)
            or not re.fullmatch(r'[a-f0-9]{64}', packet.metadata_sha256)):
        raise ValueError('Invalid canonical capture identity')
    expected_profile = {'CT': 'non_financial', 'NH': 'bank', 'CK': 'financial_other', 'BH': 'financial_other', 'UNKNOWN': 'unknown'}
    if packet.profile not in (expected_profile[packet.company_type], 'unknown'):
        raise ValueError('Incompatible canonical issuer model')
    for kind, receipt in packet.reports.items():
        if (receipt.statement != kind or len(receipt.observations) > 320
                or receipt.observed_at.tzinfo is None
                or receipt.observed_at.utcoffset() is None
                or receipt.observations and (receipt.status != 'healthy'
                    or not re.fullmatch(r'[a-f0-9]{64}', receipt.content_sha256 or ''))
                or not receipt.observations and receipt.status == 'healthy'):
            raise ValueError('Invalid canonical receipt')
        seen = set()
        for obs in receipt.observations:
            ctx = obs.source_context
            quarter = int(obs.period[-1]) if '-Q' in obs.period else None
            if (obs.ticker != packet.ticker or obs.source != packet.source or obs.statement != kind
                    or obs.period in seen or obs.frequency != ('quarterly' if quarter else 'annual')
                    or ctx is None or ctx.fiscal_year != int(obs.period[:4]) or ctx.fiscal_quarter != quarter
                    or ctx.unit_evidence != 'audited_vci_adapter_contract' or ctx.amount_multiplier != 1
                    or ctx.original_currency not in (None, 'VND') or ctx.original_unit not in (None, 'VND')
                    or ctx.display_rights == 'permitted' or ctx.display_rights_reference
                    or ctx.access_classification != 'PUBLIC_DISPLAY_REVIEW_REQUIRED'
                    or ctx.data_confidence != 'SOURCE_REPORTED' or ctx.period_start or ctx.period_end
                    or ctx.publication_time_qualified
                    or obs.consolidation != ctx.original_metadata.get('consolidation')
                    or any(obs.source_dates.get(key) != ctx.original_metadata.get(key)
                        for key in ('publicDate', 'updateDate', 'createDate'))
                    or obs.basis != ('point_in_time' if kind == 'balance' else
                        'annual' if quarter is None else ctx.original_metadata.get('flowBasis', 'standalone'))):
                raise ValueError('Invalid or promoted canonical provenance')
            seen.add(obs.period)
            if len(obs.items) > 1000 or len({line.code for line in obs.items}) != len(obs.items):
                raise ValueError('Ambiguous canonical statement lines')
            lines = {line.code: line for line in obs.items}
            if set(obs.fields) != set(MAP[kind]):
                raise ValueError('Unexpected canonical field mapping')
            for field, (code, pattern) in MAP[kind].items():
                value = obs.fields[field]
                if value is None:
                    continue
                line = lines.get(code)
                if (obs.field_codes.get(field) != code or line is None
                        or line.semantic_status != 'reported' or line.value != value or line.raw_value != value
                        or line.unit != ('VND/share' if field == 'eps_reported' else 'VND')
                        or not re.search(pattern, line.name_en.casefold().strip())
                        or field in NON_FINANCIAL_ONLY and packet.profile != 'non_financial'
                        or field in BANK_ONLY and packet.profile != 'bank'):
                    raise ValueError('Canonical amount differs from reviewed source line')
    return packet


def personal_projection(packet, *, frequency='annual', limit=8, authorization_reference):
    if (authorization_reference and not packet.is_fixture and packet.source.startswith('issuer:')
            and packet.source_version in ('reviewed-report-v2','reviewed-report-history-v1')):
        # Original reports use the existing scoped filing projection. Provider
        # captures are never enriched or overwritten with this separate source.
        full = financial_engine(packet, frequency=frequency, limit=limit)
        return display_financial_response(full,
            internal_authorization_reference=authorization_reference).model_dump(mode='json')
    if not authorization_reference or packet.is_fixture or packet.source not in ('vnstock:VCI', 'CafeF:annual-summary'):
        raise ValueError('Personal projection requires real authorized saved evidence')
    full = financial_engine(packet, frequency=frequency, limit=limit)
    public = display_financial_response(full)
    # Work on dictionaries: never mutate canonical evidence or the public result.
    out = public.model_dump(mode='json')
    out.update(display_scope='personal_research', access_classification='PERSONAL_RESEARCH',
        data_confidence='SOURCE_REPORTED', research_authorization_reference=authorization_reference,
        read_kind='saved_personal_research')
    contexts = { (kind, o.period): o for kind, r in packet.reports.items() for o in r.observations }

    def usable(ref):
        obs = contexts.get((ref.get('statement'), ref.get('period')))
        context = obs.source_context if obs else None
        return (obs and context and context.display_rights != 'prohibited'
            and (context.unit_evidence, context.amount_multiplier) == (
                ('audited_cafef_adapter_contract', 1000) if packet.source == 'CafeF:annual-summary' else ('audited_vci_adapter_contract', 1))
            and obs.basis in ('annual','standalone','point_in_time')
            and ref.get('code') and ref.get('content_sha256') and ref.get('currency') == 'VND'
            and ref.get('value') is not None and obs.fields.get(ref.get('field')) == ref['value'])

    evidence = {}
    for raw, row in zip(full.rows, out['rows']):
        states = {}
        for key, calc in raw['calculations'].items():
            refs = calc.get('inputs', [])
            # Exactly one original observation; never relabel YTD differences,
            # TTM sums, ratios or unknown-basis comparisons as reported facts.
            if (raw.get(key) is not None and not calc.get('reason') and len(refs) == 1
                    and refs[0].get('field') == key and usable(refs[0])
                    and raw[key] == refs[0]['value']):
                row[key] = raw[key]
                states[key] = dict(data_confidence='SOURCE_REPORTED', access_classification='PERSONAL_RESEARCH',
                    consolidation=refs[0].get('consolidation'), source=packet.source,
                    receipt_sha256=refs[0]['content_sha256'], source_field=refs[0]['code'])
        row['research_evidence'] = states
        evidence[row['period']] = states
    by_period = {r['period']: r for r in out['rows']}
    out['chart_rows'] = [{**r, **{k:v for k,v in by_period.get(r['period'],{}).items() if k != 'calculations'}} for r in out['chart_rows']]
    latest = out['rows'][-1] if out['rows'] else {}
    for metric in out['fundamental_summary']['metrics']:
        if metric['key'] in latest.get('research_evidence', {}):
            metric.update(value=latest[metric['key']], status='SOURCE_REPORTED', data_confidence='SOURCE_REPORTED',
                access_classification='PERSONAL_RESEARCH', consolidation=latest['research_evidence'][metric['key']]['consolidation'],
                reason='Source-reported observation; reporting basis may be UNKNOWN.', blockers=[])
    for change in out['changes']:
        # Preserve the public comparison guard. A visible observation is not a
        # certified comparison against an UNKNOWN reporting basis.
        change['current'] = latest.get(change['metric'])
    for kind, statement in out['statements'].items():
        supported = (set(code for code, _ in MAP[kind].values()) if packet.source == 'vnstock:VCI'
            else {code for o in packet.reports[kind].observations for code in o.field_codes.values()})
        # Additional statement amounts have explicit source identifiers/labels;
        # no new metric calculation or public provider mapping is introduced.
        extras = ({'isa11':r'^operating profit/\(loss\)$',
                   'isa16':r'^net accounting profit/\(loss\) before tax$'} if kind == 'income' else
                  {'bsa8':r'^accounts receivable$'} if kind == 'balance' else {}) if packet.profile == 'non_financial' else {}
        for period in statement['periods']:
            original = contexts[(kind, period['period'])]
            allowed = {ref['code'] for refs in [raw['calculations'].values() for raw in full.rows if raw['period'] == period['period']]
                for calc in refs for ref in calc.get('inputs', []) if ref['statement'] == kind and usable(ref)}
            source_lines = {line.code: line for line in original.items}
            for line in period['items']:
                src = source_lines[line['code']]
                ctx = original.source_context
                direct_unit = statement_line_unit(src.code, src.name_en) if packet.source == 'vnstock:VCI' else None
                direct_vci_line = (packet.source == 'vnstock:VCI' and ctx and ctx.display_rights != 'prohibited'
                    and ctx.unit_evidence == 'audited_vci_adapter_contract' and ctx.amount_multiplier == 1
                    and src.semantic_status == 'reported' and src.value is not None and math.isfinite(src.value)
                    and src.raw_value == src.value and src.unit in (direct_unit, 'VND')
                    and direct_unit in ('VND', 'VND/share', 'shares'))
                extra = (line['code'] in extras and re.fullmatch(extras[line['code']],src.name_en.casefold().strip())
                    and ctx and ctx.display_rights != 'prohibited' and ctx.unit_evidence == 'audited_vci_adapter_contract'
                    and original.basis in ('annual','standalone','point_in_time') and src.value is not None
                    and math.isfinite(src.value))
                # Whitelist qualified definitions, not every numeric provider
                # column for calculations. Direct VCI statement lines are safe in
                # private research when their source code, amount unit and value
                # are intact; the containing period retains standalone/YTD/balance
                # basis so a cumulative flow is never presented as a quarter flow.
                if direct_vci_line or (line['code'] in supported & allowed or extra) and src.semantic_status == 'reported':
                    line.update(value=src.value, semantic_status='reported', data_confidence='SOURCE_REPORTED', access_classification='PERSONAL_RESEARCH')
                    if direct_vci_line:
                        line['unit'] = direct_unit
                else:
                    line.update(value=None, semantic_status='unqualified', data_confidence='INVALID' if src.semantic_status=='conflicted' else 'UNVERIFIED')
            period.update(data_confidence='SOURCE_REPORTED', access_classification='PERSONAL_RESEARCH')
        # Keep only the reviewed subset in the useful table. Original source
        # definitions/receipt hashes remain inspectable; no blank filler rows.
        visible = {line['code'] for p in statement['periods'] for line in p['items'] if line['value'] is not None}
        for p in statement['periods']:
            p['items'] = [line for line in p['items'] if line['code'] in visible]
    # Existing charts reuse individual observations with explicit research status.
    # Unknown-basis amounts are never stacked as a reconciled composition.
    for panel in out['research_panels']:
        if panel['chart'] == 'performance' and (panel['key'] != 'quarterly' or frequency == 'quarterly'):
            for point in panel['rows']:
                for series in panel['series']:
                    key = series['key']
                    if key in evidence.get(point['period'], {}) and series['unit'] == 'VND':
                        point['values'][key] = by_period[point['period']][key]
                        point['statuses'][key] = 'SOURCE_REPORTED'
                        point['bases'][key] = evidence[point['period']][key]['consolidation']
            if any(v is not None for p in panel['rows'] for v in p['values'].values()):
                panel['status'] = 'SOURCE_REPORTED'
    keys = ['total_assets', 'total_liabilities', 'equity']
    out['research_panels'].append(dict(key='balance_history', title='Reported balance history', chart='performance',
        source=packet.source, frequency=frequency, status='SOURCE_REPORTED' if any(k in e for e in evidence.values() for k in keys) else 'UNAVAILABLE',
        partial=True, methodology='Separate source-reported amounts, not a reconciled or stacked composition. Reporting basis may be UNKNOWN.',
        reasons=['Source-reported financial data. Consolidation basis not independently verified.'],
        series=[dict(key=k,label={'total_assets':'Total assets','total_liabilities':'Total liabilities','equity':'Total equity'}[k],unit='VND') for k in keys],
        rows=[dict(period=r['period'], values={k:r.get(k) if k in evidence.get(r['period'],{}) else None for k in keys},
            statuses={k:'SOURCE_REPORTED' if k in evidence.get(r['period'],{}) else 'UNAVAILABLE' for k in keys},
            bases={k:evidence.get(r['period'],{}).get(k,{}).get('consolidation') for k in keys}) for r in out['chart_rows']]))
    for panel in out['research_panels']:
        bases = {p['bases'][k] for p in panel['rows'] for k,v in p['values'].items() if v is not None}
        if len(bases) > 1:
            # Keep each table observation, but never connect incompatible bases
            # in a single historical chart or treat UNKNOWN as matching known.
            for point in panel['rows']:
                for key in point['values']:
                    point['values'][key] = None
                    point['statuses'][key] = 'UNQUALIFIED'
            panel['status'] = 'UNQUALIFIED'
            panel['reasons'].append('Conflicting reporting bases')
    out['limitations'].insert(0, 'PERSONAL RESEARCH: saved source observations, not current data or provider authorization. UNKNOWN basis does not qualify derived comparisons.')
    from src.services.financial_verification import verification_assessment
    out['verification'] = verification_assessment(full, out['rows'], audience='personal_research')
    return out
