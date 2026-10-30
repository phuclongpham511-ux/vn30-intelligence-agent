"""Review observed provider classifications without inventing effective dates."""
from src.services.market_summary import audit_icb_metadata


def review_memberships(records, *, receipt, review_reference):
    if not isinstance(review_reference, str) or not review_reference.strip():
        raise ValueError('An explicit review reference is required')
    audit = audit_icb_metadata(records, receipt=receipt)
    rows = []
    for item in audit['items']:
        usable = item['status'] == 'OBSERVED_PAIR_UNQUALIFIED'
        rows.append(dict(ticker=item['symbol'], exchange=item['exchange'],
            provider_code=item['icb_code'], provider_label=item['icb_name'],
            observed_at=receipt['fetched_at'], source_record_sha256=item['record_sha256'],
            verification_status='PARTIALLY_VERIFIED' if usable else 'UNAVAILABLE',
            source_status=item['status'], taxonomy_version=None, taxonomy_level=None,
            classification_effective_at=None, financial_model=None,
            eligible_for_industry_aggregation=False))
    return dict(contract='industry-membership-review-v1', review_reference=review_reference,
        source=audit['source'], receipt=receipt, basis='observed_provider_snapshot',
        public_display_eligible=False, taxonomy_eligible=False,
        entries=rows, coverage=audit['coverage'], excluded_nonordinary_rows=audit['excluded_nonordinary_rows'],
        duplicate_rows=audit['duplicate_rows'], invalid_rows=audit['invalid_rows'],
        missing_evidence=['vendor_taxonomy_version_and_level', 'classification_effective_dates',
            'applicable_taxonomy_display_rights', 'reviewed_financial_model_mapping'],
        limitations=['Observation time is not a membership effective date.',
            'Exact provider codes and labels do not establish a hierarchy.',
            'This review dataset cannot be loaded as an IndustryTaxonomy.'])
