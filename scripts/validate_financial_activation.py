"""Offline real saved-data and in-process API verification; never starts a server."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.analytics.financial_engine import financial_engine
from src.services.financial_presentation import display_financial_response
from src.services.personal_financials import saved_packet, saved_research_packet, personal_projection
from src.services.financial_intelligence import metric_unit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(captures, report_dir, private_responses, *, limit=8, evidence='preferred'):
    root = Path(captures).resolve(strict=True)
    report = Path(report_dir)
    private = Path(private_responses).resolve()
    if any(part.casefold() in ('public', 'static') for part in private.parts):
        raise ValueError('Responses require private storage')
    report.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    index = json.loads((root / 'index.json').read_text(encoding='utf-8'))
    summaries, metric_rows, fixtures = [], [], []
    env = dict(APP_ENV='development', DATABASE_URL='sqlite://', TECHNICAL_EOD_PILOT='false',
        WOOFI_PERSONAL_RESEARCH='1', WOOFI_PERSONAL_BIND='127.0.0.1',
        WOOFI_PERSONAL_CAPTURES=str(root), WOOFI_FINANCIAL_TAXONOMY='',
        WOOFI_FINANCIAL_JOURNAL='', SSI_API_KEY='', SSI_API_SECRET='')
    # This is an ASGI test transport, not a listener, process restart or browser.
    # No lifespan is entered and no application DB/provider route is requested.
    with patch.dict(os.environ, env):
        from main import app
        client = TestClient(app, client=('127.0.0.1', 1234), base_url='http://127.0.0.1')
        for ticker in sorted(index['captures']):
            packet, digest = saved_packet(root, ticker)
            before = packet.model_dump()
            observations = [o for r in packet.reports.values() for o in r.observations]
            fixtures.append(dict(ticker=ticker, capture_sha256=digest, source=packet.source,
                source_version=packet.source_version, profile=packet.profile, company_type=packet.company_type,
                statement_observations=len(observations),
                qualified_scope=sum(o.consolidation in ('consolidated', 'standalone') for o in observations),
                original_units=sum(bool(o.source_context and o.source_context.original_unit) for o in observations),
                publication_qualified=sum(bool(o.source_context and o.source_context.publication_time_qualified) for o in observations)))
            for frequency in ('annual', 'quarterly', 'ttm'):
                packet,digest=saved_research_packet(root,ticker,frequency=frequency,evidence=evidence)
                before=packet.model_dump()
                observations=[o for r in packet.reports.values() for o in r.observations]
                engine = financial_engine(packet, frequency=frequency, limit=limit)
                public = display_financial_response(engine)
                personal = personal_projection(packet, frequency=frequency, limit=limit,
                    authorization_reference='task:financial-real-data-activation-v1:' + digest)
                response = client.get(f'/personal-research/financials/{ticker}?frequency={frequency}&limit={limit}&evidence={evidence}')
                require(response.status_code == 200, 'Saved-data API did not return evidence')
                body = response.json()
                require(body['verification'] == personal['verification'], 'API verification differs from projection')
                require(body['rows'] == personal['rows'], 'API amounts differ from projection')
                require(response.headers.get('cache-control') == 'private, no-store', 'Private response cache policy')
                require(packet.model_dump() == before, 'Canonical evidence was mutated')
                raw = {r['period']: r for r in engine.rows}
                for row in body['rows']:
                    for key in row.get('research_evidence', {}):
                        refs = raw[row['period']]['calculations'][key]['inputs']
                        require(len(refs) == 1 and refs[0]['field'] == key
                            and refs[0]['value'] == row[key], 'Displayed amount is not one reported source observation')
                    for key in ('roe', 'roa', 'gross_margin', 'net_margin', 'loan_deposit_ratio',
                            'current_ratio', 'quick_ratio'):
                        if any(o.consolidation is None for o in observations):
                            require(row[key] is None, 'Unknown basis cannot activate a derived ratio')
                for period in body['verification']['periods']:
                    for key, state in period['metrics'].items():
                        metric_rows.append(dict(ticker=ticker, frequency=frequency, period=period['period'],
                            metric_id=key, unit=metric_unit(key), verification_status=state['status'],
                            display_eligible=state['display_eligible'],
                            public_display_eligible=state['public_display_eligible'],
                            missing_evidence=';'.join(state['missing_evidence']), source=packet.source,
                            capture_sha256=digest))
                panels = {}
                for panel in body['research_panels']:
                    if panel['key'] in ('cashflow', 'profitability', 'liquidity', 'bank_funding'):
                        panels[panel['key']] = dict(status=panel['status'],
                            points=sum(v is not None for r in panel['rows'] for v in r['values'].values()),
                            series=[s['key'] for s in panel['series']])
                summaries.append(dict(ticker=ticker, frequency=frequency,source=packet.source,
                    periods=[r['period'] for r in body['rows']],
                    displayed_metric_ids=body['verification']['displayed_metric_ids'],
                    verification_counts=body['verification']['statuses'],
                    public_visible_values=sum(r.get(k) is not None for r in public.rows for k in raw[r['period']]['calculations']),
                    panels=panels))
                (private / f'{ticker}-{frequency}.json').write_text(json.dumps(body), encoding='utf-8')
        require(client.get('/personal-research/financials/NOTCOVERED').status_code == 404, 'Uncovered ticker must stay missing')
        first_ticker = next(iter(index['captures']))
        require(client.get(f'/personal-research/financials/{first_ticker}', headers={'Host': 'foreign.invalid'}).status_code == 404,
            'Foreign Host must not authorize local financial data')
        directory = client.get('/financial-intelligence/industries').json()
        require(directory['status'] == 'UNAVAILABLE' and directory['industries'] == [], 'No taxonomy should be invented')
    with (report / 'REAL_METRIC_ACTIVATION_MATRIX.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(metric_rows[0])); writer.writeheader(); writer.writerows(metric_rows)
    public_count = sum(p['public_visible_values'] for p in summaries)
    result = dict(contract='real-financial-activation-validation-v1',
        observed_at=datetime.now(timezone.utc).isoformat(), status='PASS',
        transport='in-process ASGI; no runtime listener or browser', runtime_status='PENDING',
        provider_requests=0, auth_requests=0, application_database_access=False,
        period_limit=limit, issuers=fixtures, projections=summaries,
        matrix_counts=dict(Counter(r['verification_status'] for r in metric_rows)),
        public_qualified_observations=public_count,
        limitations=['Saved source observations are not current provider freshness.',
            'Original transport is not independently reconstructed from canonical-only captures.',
            'API and contract checks are not browser or post-restart runtime acceptance.'])
    (report / 'REAL_DATA_API_VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (report / 'REAL_DATA_FIXTURE_MANIFEST.json').write_text(json.dumps(dict(
        contract='real-financial-fixture-manifest-v1', issuers=fixtures), indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True)
    parser.add_argument('--report-dir', required=True)
    parser.add_argument('--private-responses', required=True)
    parser.add_argument('--limit', type=int, default=8, choices=range(1, 21))
    parser.add_argument('--evidence',choices=('preferred','provider'),default='preferred')
    args = parser.parse_args()
    result = validate(args.captures, args.report_dir, args.private_responses, limit=args.limit,evidence=args.evidence)
    print(json.dumps(dict(status=result['status'], projections=len(result['projections']),
        matrix_counts=result['matrix_counts'],
        public_qualified_observations=result['public_qualified_observations'], provider_requests=0)))
