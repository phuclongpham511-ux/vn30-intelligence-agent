"""Long-form projection of the canonical engine, with its public evidence gates."""
from src.analytics.financial_engine import financial_engine
from src.providers.vnstock.financial_statements import MAP, content_hash
from src.schemas.financial_intelligence import MetricObservation
from src.services.financial_presentation import metric_status, inputs_reasons

MULTIPLES = {'debt_equity','current_ratio','quick_ratio','cash_conversion','inventory_turnover','asset_turnover'}
FRACTIONS = {'gross_margin','net_margin','roe','roa','liabilities_assets','loan_deposit_ratio'}


def metric_unit(key):
    return ('VND/share' if key == 'eps_reported' else 'multiple' if key in MULTIPLES else
        'fraction' if key in FRACTIONS or '_growth_' in key else 'VND')


def normalized_metrics(packet, *, frequency='annual', limit=20):
    result = financial_engine(packet, frequency=frequency, limit=limit)
    invalid_balances = set()
    for obs in packet.reports['balance'].observations:
        a,l,e = (obs.fields.get(k) for k in ('total_assets','total_liabilities','equity'))
        if None not in (a,l,e) and abs(a-l-e) > max(1, abs(a)*1e-6):
            invalid_balances.add(obs.period)
    raw_fields = {field for fields in MAP.values() for field in fields}
    observations = []
    for row in result.rows:
        for key, evidence in row['calculations'].items():
            refs = evidence.get('inputs', [])
            status, reason = metric_status(row, key, result)
            reasons = list(dict.fromkeys(([reason] if reason else []) + (inputs_reasons(
                refs, result.source, fixture=packet.is_fixture) if status not in ('QUALIFIED','DEMO') else [])))
            # The existing engine keeps source amounts inspectable. This normalized
            # comparison boundary additionally excludes contradictory identities.
            if any(r['statement']=='balance' and r['period'] in invalid_balances for r in refs):
                status = 'INVALID'
                reasons.append('balance_identity_failed')
            current_refs = [r for r in refs if r['period'] == row['period']]
            scopes = {r.get('consolidation') for r in refs}
            scope = next(iter(scopes)) if len(scopes)==1 and scopes <= {'consolidated','standalone'} else 'unknown'
            contexts = [r.get('source_context') or {} for r in current_refs]
            starts = {c.get('period_start') for c in contexts}
            ends = {c.get('period_end') for c in contexts}
            # No synthetic calendar boundaries or publication timestamps. TTM
            # boundaries need their own qualified start, not the latest quarter.
            start = next(iter(starts)) if frequency!='ttm' and len(starts)==1 else None
            end = next(iter(ends)) if len(ends)==1 else None
            receipts = [packet.reports[r['statement']].observed_at for r in refs]
            fetched = max(receipts or [r.observed_at for r in packet.reports.values()])
            reported = key in raw_fields and len(refs)==1 and refs[0].get('field')==key and row[key]==refs[0].get('value')
            kind = 'unavailable' if row.get(key) is None else 'reported' if reported else 'derived'
            value = row.get(key) if status in ('QUALIFIED','DEMO') else None
            observations.append(MetricObservation(ticker=packet.ticker, metric_id=key,
                value=value,
                unit=metric_unit(key), period=row['period'], period_start=start, period_end=end,
                period_type=frequency, fiscal_year=int(row['period'][:4]),
                fiscal_quarter=int(row['period'][-1]) if '-Q' in row['period'] else None,
                report_scope=scope, source=packet.source, fetched_at=fetched, published_at=None,
                revision=content_hash(dict(inputs=refs,formula=evidence['formula'],source_version=packet.source_version,
                    value=value,metric_kind=kind,quality_status=status,quality_reasons=reasons,
                    period_start=start,period_end=end,report_scope=scope)),
                metric_kind=kind,
                quality_status=status,quality_reasons=reasons,formula=evidence['formula'],
                profile=packet.profile,company_type=packet.company_type,is_fixture=packet.is_fixture,input_refs=refs))
    return observations
