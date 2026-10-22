"""Source-reported bank ratios with reviewed page evidence; no inferred formula."""
from decimal import Decimal
import re
from typing import Literal

from pydantic import Field

from src.providers.financial_filings import StrictEvidence
from src.providers.reviewed_reports import Quote, ReviewedReport
from src.providers.vnstock.financial_statements import content_hash
from src.schemas.financial_intelligence import MetricObservation


class ReportedRatio(StrictEvidence):
    metric_id: Literal['nim', 'car', 'cir', 'cost_of_funds']
    original_label: str = Field(min_length=1, max_length=200)
    period: str = Field(pattern=r'^\d{4}$')
    raw_token: str = Field(pattern=r'^\d{1,3}(?:\.\d{1,4})?%$')
    source_row: Quote
    period_quote: Quote


class RatioReview(StrictEvidence):
    contract: Literal['reported-bank-ratio-review-v57']
    ticker: str
    document_sha256: str
    ratios: list[ReportedRatio] = Field(min_length=1, max_length=10)


def reported_ratio_facts(review, report_manifest, packet):
    """A quoted percentage is evidence, not a verified canonical definition.

    The original report adapter must have authenticated all cited page text and
    rendered images first. Facts remain UNQUALIFIED with their source value in
    input_refs, never a display value or a recalculated Financial Engine metric.
    """
    review = RatioReview.model_validate(review)
    report = ReviewedReport.model_validate(report_manifest)
    if (packet.profile != 'bank' or review.ticker != packet.ticker or review.ticker != report.ticker
            or review.document_sha256 != report.document_sha256):
        raise ValueError('Reported bank ratio document/issuer mismatch')
    pages = {p.number: p.text for p in report.pages}
    facts = []
    for ratio in review.ratios:
        for quote in (ratio.source_row, ratio.period_quote):
            if quote.page not in pages or quote.text not in pages[quote.page]:
                raise ValueError('Reported ratio lacks a reviewed source quote')
        if (ratio.original_label not in ratio.source_row.text or ratio.period not in ratio.period_quote.text
                or not re.search(r'(?<![\d.])' + re.escape(ratio.raw_token) + r'(?![\d.])', ratio.source_row.text)):
            raise ValueError('Reported ratio label, token or period is unsubstantiated')
        number = Decimal(ratio.raw_token[:-1]) / 100
        if not 0 <= number <= 1:
            raise ValueError('Reported bank ratio is outside a percentage range')
        receipt = packet.reports['income']
        if ratio.period not in {o.period for o in receipt.observations}:
            raise ValueError('Reported ratio period lacks an authenticated report receipt')
        ref = dict(ticker=packet.ticker, source=packet.source, statement='income', period=ratio.period,
            field=ratio.metric_id, value=float(number), unit='fraction',
            content_sha256=receipt.content_sha256, document_sha256=report.document_sha256,
            document_url=report.document_url, page=ratio.source_row.page,
            original_label=ratio.original_label, original_value=ratio.raw_token,
            original_unit='percent', source_row=ratio.source_row.model_dump(),
            period_quote=ratio.period_quote.model_dump(), definition_status='UNVERIFIED',
            consolidation=None, source_context=dict(display_rights='unreviewed',
                access_classification='PUBLIC_DISPLAY_REVIEW_REQUIRED'))
        facts.append(MetricObservation(ticker=packet.ticker, source=packet.source,
            metric_id=ratio.metric_id, value=None, unit='fraction', period=ratio.period,
            period_type='annual', fiscal_year=int(ratio.period), report_scope='unknown',
            fetched_at=receipt.observed_at, revision=content_hash(ref), metric_kind='reported',
            quality_status='UNQUALIFIED', quality_reasons=['reported_definition_or_scope_unverified',
                'public_display_rights_unreviewed'], formula='source-reported ' + ratio.original_label,
            profile=packet.profile, company_type=packet.company_type, input_refs=[ref]))
    return facts
