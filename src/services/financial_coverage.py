"""Read-only, evidence-labelled coverage planning over the V5.5 journal."""
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path

from src.analytics.financial_engine import quarterly, serial
from src.services.financial_journal import MetricJournal


MEMBERSHIP_FILE = Path(__file__).with_name('financial_index_memberships.json')
STATEMENTS = ('income', 'balance', 'cash')
FREQUENCIES = ('annual', 'quarterly')
CORE_METRICS = {
    'revenue': 'income', 'net_profit': 'income', 'gross_margin': 'income',
    'roe': 'balance', 'roa': 'balance', 'eps_reported': 'income',
    'total_liabilities': 'balance', 'equity': 'balance',
    'cash_operating': 'cash', 'current_ratio': 'balance',
    'revenue_growth_yoy': 'income', 'net_profit_growth_yoy': 'income',
    'pe': None, 'pb': None,
}
ORDINARY_METRICS = {'gross_margin', 'current_ratio'}
SPECIALIST = {
    'bank': ('nim', 'casa', 'npl', 'loan_loss_coverage',
             'car', 'cir', 'cost_of_funds', 'credit_growth',
             'deposit_growth', 'regulatory_ldr'),
    'securities': ('margin_lending', 'brokerage_revenue', 'fvtpl',
                   'proprietary_trading_results', 'financial_assets',
                   'borrowings', 'operating_performance'),
    'real_estate': ('inventory', 'buyer_advances', 'borrowings', 'receivables',
                    'project_information', 'presales_backlog'),
}
SOURCE_FIELDS = {
    'npl': 'npl_classified_ratio',
    'loan_loss_coverage': 'classified_loan_coverage',
    'credit_growth': 'customer_loans_growth_yoy',
    'deposit_growth': 'customer_deposits_growth_yoy',
    'inventory': 'inventory',
}
INDUSTRY_LABELS = {
    'Ngân hàng': 'bank',
    'Môi giới chứng khoán': 'securities',
    'Bất động sản': 'real_estate',
}


def membership_snapshot(as_of, path=MEMBERSHIP_FILE):
    """Select a dated complete list; keep older lists queryable."""
    value = date.fromisoformat(str(as_of))
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    if document.get('contract') != 'financial-index-membership-v1':
        raise ValueError('Unknown index membership contract')
    snapshots = document.get('snapshots', [])
    dates = [date.fromisoformat(s['effective_date']) for s in snapshots]
    if dates != sorted(set(dates)):
        raise ValueError('Membership snapshots must have unique increasing effective dates')
    for item in snapshots:
        vn30, middle, vn100 = (item[k] for k in ('vn30', 'vnmidcap', 'vn100'))
        if (len(vn30), len(middle), len(vn100)) != (30, 70, 100) or any(
            len(group) != len(set(group)) for group in (vn30, middle, vn100)
        ) or set(vn30) & set(middle) or set(vn100) != set(vn30) | set(middle):
            raise ValueError('Incomplete or inconsistent HOSE constituent list')
    eligible = [s for s in snapshots if date.fromisoformat(s['effective_date']) <= value]
    return eligible[-1] if eligible else None


def ticker_membership(ticker, *, as_of, path=MEMBERSHIP_FILE):
    """Never infer membership before a dated list is available."""
    snapshot = membership_snapshot(as_of, path)
    if snapshot is None:
        return dict(ticker=ticker, status='UNKNOWN', effective_date=None, source=None)
    status = ('CONFIRMED_VN30' if ticker in snapshot['vn30'] else
              'CONFIRMED_VN100_ONLY' if ticker in snapshot['vn100'] else
              'NOT_IN_DATED_SNAPSHOT')
    return dict(ticker=ticker, status=status, effective_date=snapshot['effective_date'],
                source=snapshot['source'])


def period_span(periods, frequency):
    periods = sorted(set(periods))
    if not periods:
        return dict(earliest=None, latest=None, count=0, missing_between=[])
    if frequency == 'annual':
        missing = [str(y) for y in range(int(periods[0]), int(periods[-1]) + 1) if str(y) not in periods]
    else:
        observed = {serial(p) for p in periods}
        missing = [quarterly(n) for n in range(min(observed), max(observed) + 1) if n not in observed]
    return dict(earliest=periods[0], latest=periods[-1], count=len(periods), missing_between=missing)


def _industry_records(document):
    if document is None:
        return {}
    if document.get('contract') != 'industry-membership-review-v1':
        raise ValueError('Unknown observed industry classification contract')
    result = {}
    for entry in document.get('entries', []):
        if entry.get('source_status') != 'OBSERVED_PAIR_UNQUALIFIED' or entry.get('exchange') != 'HOSE':
            continue
        if entry['ticker'] in result:
            raise ValueError('Ambiguous observed industry classification')
        result[entry['ticker']] = entry
    return result


def _selected_observations(journal):
    """One selected revision per source/statement/period/scope/basis."""
    with journal.connect() as db:
        rows = db.execute('''SELECT s.ticker,s.source,s.statement,s.period,s.frequency,
                s.capture_id,c.capture_sha256,c.header,o.payload
            FROM financial_selection s
            JOIN financial_statement o ON o.capture_id=s.capture_id
                AND o.statement=s.statement AND o.period=s.period
            JOIN financial_capture c ON c.id=s.capture_id
            ORDER BY s.ticker,s.source,s.statement,s.period,s.scope,s.basis''').fetchall()
    return rows


def _public_eligible(observation):
    context = observation.get('source_context') or {}
    return (context.get('display_rights') == 'permitted'
            and context.get('access_classification') == 'PUBLIC_DISPLAY_APPROVED')


def _metric_state(facts, field_observations, statement):
    if facts and not field_observations and all(
        'reported_definition_or_scope_unverified' in f.get('quality_reasons', []) for f in facts
    ):
        return 'PARTIAL', 'reported_definition_or_scope_unverified'
    if any(f['quality_status'] == 'QUALIFIED' and f['value'] is not None for f in facts):
        return 'AVAILABLE', 'qualified_calculation_or_reported_fact'
    if any(f['metric_kind'] == 'reported' and any(r.get('value') is not None for r in f['input_refs'])
           for f in facts):
        return 'AVAILABLE', 'source_reported_value_display_withheld'
    if any(field_observations):
        return 'AVAILABLE', 'selected_source_field_present'
    if any(f['input_refs'] for f in facts):
        return 'PARTIAL', 'calculation_inputs_incomplete_or_unqualified'
    if statement is None:
        return 'UNKNOWN', 'unsupported_or_unmapped_metric_definition'
    return 'MISSING', 'not_in_selected_source_observations'


def _fact_matches_selection(fact, selected_receipts):
    """Exclude metric vintages whose source receipt is no longer selected."""
    if not fact.input_refs:
        return False
    for ref in fact.input_refs:
        key = (fact.ticker, ref.get('source', fact.source), ref.get('statement'),
               ref.get('period'))
        if ref.get('content_sha256') not in selected_receipts.get(key, set()):
            return False
    return True


def build_coverage(journal_path, *, as_of, industry_snapshot=None, membership_path=MEMBERSHIP_FILE):
    """Produce a refreshable inventory and backlog without altering source rows."""
    selected = membership_snapshot(as_of, membership_path)
    if selected is None:
        raise ValueError('No confirmed index membership effective on this date')
    journal = MetricJournal(journal_path, readonly=True)
    industry = _industry_records(industry_snapshot)
    rows_by_ticker = defaultdict(list)
    selected_receipts = defaultdict(set)
    primary = {}
    for ticker, source, kind, period, frequency, capture_id, digest, header, payload in _selected_observations(journal):
        obs = json.loads(payload)
        meta = json.loads(header)
        receipt = meta['reports'][kind]
        context = obs.get('source_context') or {}
        original = context.get('original_metadata') or {}
        fixture = bool(meta.get('is_fixture'))
        if not fixture:
            selected_receipts[(ticker, source, kind, period)].update(
                (receipt.get('content_sha256'), original.get('original_receipt_sha256')))
        rows_by_ticker[ticker].append(dict(source=source, statement=kind, period=period,
            frequency=frequency, capture_id=capture_id, capture_sha256=digest,
            receipt=receipt, observation=obs, is_fixture=fixture))
        if not fixture and (source == 'vnstock:VCI' or ticker not in primary):
            primary[ticker] = dict(source=source, profile=meta['profile'], company_type=meta['company_type'])
    # Existing journal selection already resolves revisions of one metric identity.
    # Other sources remain separate evidence; no cross-provider reconciliation.
    fact_index = defaultdict(list)
    for fact in journal.read():
        if not fact.is_fixture and _fact_matches_selection(fact, selected_receipts):
            fact_index[(fact.ticker, fact.source, fact.period, fact.metric_id)].append(
                fact.model_dump(mode='json'))
    all_periods = {'annual': set(), 'quarterly': set()}
    for rows in rows_by_ticker.values():
        for row in rows:
            if not row['is_fixture']:
                all_periods[row['frequency']].add(row['period'])
    reference = {f: max(values) if values else None for f, values in all_periods.items()}
    current30, current100 = set(selected['vn30']), set(selected['vn100'])
    companies, backlog = [], []
    for ticker in selected['vn30'] + [t for t in selected['vn100'] if t not in current30]:
        all_rows = rows_by_ticker.get(ticker, [])
        own = [r for r in all_rows if not r['is_fixture']]
        fixture_ids = sorted({r['capture_id'] for r in all_rows if r['is_fixture']})
        has_values = any(item.get('value') is not None
                         for row in own for item in row['observation']['items'])
        profile = primary.get(ticker, {})
        label = industry.get(ticker, {})
        model = INDUSTRY_LABELS.get(label.get('provider_label'))
        if model is None and profile.get('company_type') == 'NH':
            model = 'bank'
        if model is None and profile.get('company_type') == 'CK':
            model = 'securities'
        model = model or 'unknown'
        by_family = {}
        observed_fields = defaultdict(list)
        for row in own:
            obs = row['observation']
            for field, value in obs['fields'].items():
                if value is not None:
                    observed_fields[(row['period'], field)].append(row)
        for kind in STATEMENTS:
            by_family[kind] = {}
            for frequency in FREQUENCIES:
                group = [r for r in own if r['statement'] == kind and r['frequency'] == frequency]
                periods = {r['period'] for r in group}
                valued = {r['period'] for r in group if any(
                    item.get('value') is not None for item in r['observation']['items'])}
                status = ('MISSING' if not group else 'SOURCE_UNAVAILABLE' if not valued
                          else 'PARTIAL' if len(valued) < len(periods) else 'AVAILABLE')
                line_detail = defaultdict(list)
                for row in group:
                    items = row['observation']['items']
                    line_detail[row['period']].append(dict(source=row['source'],
                        capture_id=row['capture_id'],
                        available_codes=sorted(i['code'] for i in items if i.get('value') is not None),
                        unavailable_codes=sorted(i['code'] for i in items if i.get('value') is None),
                        non_vnd_units={i['code']: i['unit'] for i in items if i.get('unit') != 'VND'},
                        source_unit=(row['observation'].get('source_context') or {}).get('original_unit')))
                by_family[kind][frequency] = dict(status=status, **period_span(valued, frequency),
                    observed_periods=len(periods), source_line_values=sum(
                        item.get('value') is not None for r in group for item in r['observation']['items']),
                    detailed_source_lines=sum(len(r['observation']['items']) for r in group),
                    public_display_eligible=any(_public_eligible(r['observation']) for r in group),
                    source_lines_by_period=dict(sorted(line_detail.items())),
                    sources=sorted({r['source'] for r in group}),
                    capture_ids=sorted({r['capture_id'] for r in group}))
        metric_periods = {}
        for period in sorted({r['period'] for r in own}):
            metric_periods[period] = {}
            for metric, kind in CORE_METRICS.items():
                facts = [f for source in {r['source'] for r in own}
                         for f in fact_index.get((ticker, source, period, metric), [])]
                direct = observed_fields.get((period, metric), [])
                status, reason = _metric_state(facts, direct, kind)
                issuer_profile = profile.get('profile')
                if metric in ORDINARY_METRICS and issuer_profile not in (None, 'non_financial'):
                    status, reason = 'NOT_APPLICABLE', 'not_applicable_to_issuer'
                elif metric in ORDINARY_METRICS and issuer_profile is None:
                    status, reason = 'UNKNOWN', 'issuer_profile_unconfirmed'
                metric_periods[period][metric] = dict(status=status, reason=reason,
                    reported=bool(direct or any(f['metric_kind'] == 'reported' for f in facts)),
                    calculated=any(f['metric_kind'] == 'derived' for f in facts),
                    sources=sorted({r['source'] for r in direct} | {f['source'] for f in facts}),
                    units=sorted({f['unit'] for f in facts} | {
                        r['observation']['source_context']['original_unit']
                        for r in direct if r['observation'].get('source_context')
                        and r['observation']['source_context'].get('original_unit')}),
                    definitions=sorted({f['formula'] for f in facts}),
                    capture_ids=sorted({r['capture_id'] for r in direct}),
                    public_display_eligible=any(f['quality_status'] == 'QUALIFIED' and f['value'] is not None
                        and all((r.get('source_context') or {}).get('display_rights') == 'permitted'
                                for r in f['input_refs']) for f in facts))
        for frequency in FREQUENCIES:
            periods = [p for p in metric_periods if ('-Q' in p) == (frequency == 'quarterly')]
            if not periods:
                continue
            period = max(periods)
            for metric, cell in metric_periods[period].items():
                if cell['status'] in ('AVAILABLE', 'NOT_APPLICABLE'):
                    continue
                backlog.append(dict(task_id=f'financial:{ticker}:{frequency}:{metric}',
                    priority='P4', ticker=ticker, family=metric, frequency=frequency,
                    missing_periods=[period], industry=model,
                    suggested_source_category='issuer_filing_or_licensed_financial_provider',
                    source_availability='UNTESTED', reason=cell['reason'],
                    definition_status=('UNRESOLVED' if cell['status'] == 'UNKNOWN' else 'REVIEWED_OR_REPORTED')))
        specialist = {}
        latest = reference['quarterly'] or reference['annual']
        for category, metrics in SPECIALIST.items():
            for metric in metrics:
                if metric in specialist and model != category:
                    continue
                if model != category:
                    specialist[metric] = dict(status='NOT_APPLICABLE' if model != 'unknown' else 'UNKNOWN',
                        reason='different_industry' if model != 'unknown' else 'industry_unconfirmed')
                    continue
                alias = SOURCE_FIELDS.get(metric, metric)
                by_period = {}
                for period in sorted({r['period'] for r in own}):
                    facts = [f for source in {r['source'] for r in own}
                             for f in fact_index.get((ticker, source, period, alias), [])]
                    direct = observed_fields.get((period, alias), [])
                    components = (observed_fields.get((period, 'short_debt'), [])
                                  + observed_fields.get((period, 'long_debt'), [])) if metric == 'borrowings' and model == 'real_estate' else []
                    status, reason = _metric_state(facts, direct, None)
                    if components:
                        both = all(observed_fields.get((period, field)) for field in ('short_debt', 'long_debt'))
                        status, reason = ('AVAILABLE', 'both_source_borrowing_components_present') if both else (
                            'PARTIAL', 'one_source_borrowing_component_present')
                    if status == 'UNKNOWN':
                        status, reason = 'MISSING', 'no_verified_mapping_in_saved_source'
                    by_period[period] = dict(status=status, reason=reason,
                        frequency='quarterly' if '-Q' in period else 'annual',
                        sources=sorted({r['source'] for r in direct + components} | {f['source'] for f in facts}),
                        units=sorted({f['unit'] for f in facts} | {
                            r['observation']['source_context']['original_unit']
                            for r in direct + components if (r['observation'].get('source_context') or {}).get('original_unit')}),
                        definitions=sorted({f['formula'] for f in facts}),
                        capture_ids=sorted({r['capture_id'] for r in direct + components}),
                        source_fields=sorted(({alias} if direct else set()) | {
                            field for field in ('short_debt', 'long_debt')
                            if observed_fields.get((period, field)) and metric == 'borrowings'
                            and model == 'real_estate'}),
                        reported=bool(direct or components or any(f['metric_kind'] == 'reported' for f in facts)),
                        calculated=any(f['metric_kind'] == 'derived' for f in facts),
                        public_display_eligible=any(_public_eligible(r['observation']) for r in direct + components))
                assessed = by_period.get(latest, dict(status='MISSING', reason='reference_period_not_saved'))
                status, reason = assessed['status'], assessed['reason']
                specialist[metric] = dict(status=status, reason=reason,
                    reference_period=latest, reference_period_release_verified=False,
                    by_period=by_period,
                    historical_available_periods=sorted(p for p, cell in by_period.items() if cell['status'] == 'AVAILABLE'),
                    historical_source_periods=sorted(p for p, cell in by_period.items() if cell['source_fields']),
                    definition={'npl': 'loan grades 3-5 / classified customer loans',
                        'loan_loss_coverage': 'allowance / classified non-performing loans',
                        'regulatory_ldr': 'regulatory LDR; accounting loan/deposit ratio is not substituted',
                        'casa': 'verified CASA definition required; demand-deposit share is not substituted'
                        }.get(metric))
                if status != 'AVAILABLE' and has_values:
                    backlog.append(dict(task_id=f'financial:{ticker}:{metric}',
                        priority='P2', ticker=ticker, family=metric,
                        missing_periods=[latest] if latest else [], industry=model,
                        suggested_source_category='issuer_filing_or_verified_specialist_provider',
                        source_availability='UNTESTED', reason=reason))
        for kind in STATEMENTS:
            for frequency in FREQUENCIES:
                summary = by_family[kind][frequency]
                missing = list(summary['missing_between'])
                newer_observed_elsewhere = bool(reference[frequency] and reference[frequency] not in {
                    r['period'] for r in own if r['statement'] == kind and r['frequency'] == frequency
                    and any(i.get('value') is not None for i in r['observation']['items'])})
                limited_history = frequency == 'quarterly' and 0 < summary['count'] < 8
                if not (missing or newer_observed_elsewhere or limited_history or summary['count'] == 0):
                    continue
                priority = ('P0' if ticker in current30 and summary['count'] == 0 else
                            'P1' if ticker in current30 and frequency == 'quarterly' else
                            'P3' if ticker not in current30 else 'P4')
                family = f'{frequency}_{kind}'
                backlog.append(dict(task_id=f'financial:{ticker}:{family}',
                    priority=priority, ticker=ticker,
                    family=family, missing_periods=sorted(set(missing)),
                    candidate_reference_period=reference[frequency] if newer_observed_elsewhere else None,
                    reference_period_release_verified=False,
                    industry=model, suggested_source_category='issuer_filing_or_licensed_financial_provider',
                    source_availability='UNTESTED',
                    reason=('no_saved_statement' if summary['count'] == 0 else
                        'internal_period_gap' if missing else 'limited_quarterly_history'
                        if limited_history else 'newer_period_seen_elsewhere_release_unverified')))
        companies.append(dict(ticker=ticker, indices=['VN30', 'VN100'] if ticker in current30 else ['VN100'],
            membership_status='CONFIRMED_AS_OF_SNAPSHOT', membership_effective_date=selected['effective_date'],
            industry=dict(model=model, provider_label=label.get('provider_label'),
                provider_code=label.get('provider_code'), observed_at=label.get('observed_at'),
                classification_status=('PARTIALLY_VERIFIED' if label else
                    'SOURCE_PACKET_COMPANY_TYPE' if profile.get('company_type') in ('NH', 'CK') else 'UNKNOWN')),
            represented_in_sqlite=bool(all_rows), financial_data_present=has_values,
            fixture_capture_ids=fixture_ids, fixture_only=bool(fixture_ids and not own),
            sources=sorted({r['source'] for r in own}),
            statements=by_family, metrics_by_period=metric_periods, specialist_kpis=specialist))
    backlog.sort(key=lambda x:(x['priority'], x['ticker'], x['family']))
    return dict(contract='financial-coverage-v56', as_of=str(as_of), readonly=True,
        membership=dict(effective_date=selected['effective_date'], source=selected['source'],
            source_sha256=selected['source_sha256'], historical_snapshots=[s['effective_date'] for s in
                json.loads(Path(membership_path).read_text(encoding='utf-8'))['snapshots']
                if s['effective_date'] <= str(as_of)], vn30_confirmed=len(current30), vn100_confirmed=len(current100),
            subsequent_membership_changes_verified=False),
        reference_periods=reference, companies=companies,
        industry_evidence=(dict(source=industry_snapshot.get('source'),
            review_reference=industry_snapshot.get('review_reference'),
            receipt=industry_snapshot.get('receipt'),
            classification_effective_date_verified=False,
            public_display_eligible=False) if industry_snapshot else None),
        summary=dict(financial_tickers_covered=sum(c['financial_data_present'] for c in companies),
            companies_represented_in_sqlite=sum(c['represented_in_sqlite'] for c in companies),
            fixture_only_tickers=[c['ticker'] for c in companies if c['fixture_only']],
            tickers_missing=[c['ticker'] for c in companies if not c['financial_data_present']],
            industry_counts=dict(Counter(c['industry']['model'] for c in companies)),
            backlog_counts=dict(Counter(task['priority'] for task in backlog))),
        acquisition_backlog=backlog,
        limitations=['Index membership is confirmed for the dated HOSE snapshot, not continuously through as_of.',
            'Observed SSI industry labels have no verified taxonomy version or effective date.',
            'A stored source value does not establish public display permission.',
            'Missing from the journal does not prove unavailable at an external source.',
            'Reference periods come from saved data and are planning hints, not issuer filing deadlines.',
            'Specialist KPI names without a reviewed mapping remain acquisition gaps.'])
