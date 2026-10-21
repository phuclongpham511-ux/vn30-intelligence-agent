"""Explicit period selection from pinned originals; no field/source splicing.

Every original manifest remains available. One document owns each entire period.
Cross-document derived calculations are withheld by the canonical engine.
"""
import json
from pydantic import Field
from typing import Literal
from src.providers.financial_filings import StrictEvidence
from src.providers.reviewed_reports import pinned_file, report_packet
from src.providers.vnstock.financial_statements import content_hash, MAP
from src.schemas.financials import FinancialPacket, StatementReceipt


class Document(StrictEvidence):
    file: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class History(StrictEvidence):
    contract: Literal['reviewed-report-history-v1']
    ticker: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    source: str = Field(pattern=r'^issuer:[A-Za-z0-9_.-]+:reviewed-history$')
    review_reference: str = Field(min_length=1, max_length=300)
    issuer_names: list[str] = Field(min_length=1, max_length=20)
    documents: list[Document] = Field(min_length=2, max_length=20)
    # Each year selects the document hash, including overlaps. Never choose by
    # fetch time, fill individual missing cells or discard original revisions.
    selected_periods: dict[str, str]


def history_packet(manifest, root):
    e=History.model_validate(manifest)
    packets={};owners=set();names=set();periods=set()
    for d in e.documents:
        if d.sha256 in packets:raise ValueError('Duplicate history document')
        raw=json.loads(pinned_file(root,d.file,d.sha256,2_000_000))
        packet,_=report_packet(raw,root)
        if packet.ticker!=e.ticker:raise ValueError('History owner mismatch')
        names.add(raw['issuer'])
        owners.add((packet.profile,packet.company_type,raw['scope']))
        # A collection names the issuer, not a new independent provider.
        if packet.source.split(':')[1]!=e.source.split(':')[1]:raise ValueError('History provider mismatch')
        packets[d.sha256]=packet
        periods.update(o.period for r in packet.reports.values() for o in r.observations)
    if len(owners)!=1 or set(e.issuer_names)!=names or set(e.selected_periods)!=periods:
        raise ValueError('Ambiguous history owner, scope or period selection')
    selected={k:[] for k in MAP}
    for period,digest in sorted(e.selected_periods.items()):
        packet=packets.get(digest)
        if packet is None:raise ValueError('Unpinned selected document')
        found=False
        for kind,receipt in packet.reports.items():
            for original in receipt.observations:
                if original.period!=period:continue
                found=True
                obs=original.model_copy(deep=True)
                meta=obs.source_context.original_metadata
                meta.update(history_selection=e.review_reference,original_document_source=original.source,
                    original_receipt_sha256=receipt.content_sha256,original_observed_at=receipt.observed_at.isoformat())
                obs.source=e.source
                selected[kind].append(obs)
        if not found:raise ValueError('Selected document has no selected period')
    last=next(iter(packets.values()))
    reports={}
    for kind,observations in selected.items():
        latest=max((p.reports[kind] for p in packets.values()),key=lambda r:r.observed_at)
        # A collection must not suggest that every period came from whichever
        # PDF happened to be fetched last. Period contexts retain exact PDFs.
        index_url=(observations[-1].source_context.original_metadata['discovery_url']
            if observations else latest.source_url)
        reports[kind]=StatementReceipt(statement=kind,status='healthy' if observations else 'unavailable',
            observations=observations,observed_at=latest.observed_at,source_url=index_url,
            content_sha256=content_hash([o.model_dump(mode='json') for o in observations]))
    return FinancialPacket(ticker=e.ticker,source=e.source,source_version=e.contract,
        profile=last.profile,company_type=last.company_type,metadata_sha256=content_hash(e.model_dump()),reports=reports)
