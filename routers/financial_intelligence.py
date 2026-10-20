"""Read-only, opt-in journal queries. Never invokes providers or ingestion."""
from datetime import date, datetime
import os
from pathlib import Path
import sqlite3
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Response
from src.schemas.financial_intelligence import IndustryTaxonomy
from src.services.financial_journal import MetricJournal
from src.analytics.industry_financials import industry_snapshot

router=APIRouter(prefix='/financial-intelligence',tags=['Financial intelligence'])


def taxonomy_read():
    configured=os.getenv('WOOFI_FINANCIAL_TAXONOMY')
    if not configured:
        return None
    try:
        path=Path(configured)
        if path.stat().st_size>2_000_000:
            raise ValueError('Taxonomy exceeds bound')
        return IndustryTaxonomy.model_validate_json(path.read_text(encoding='utf-8'))
    except (ValueError,OSError):
        raise HTTPException(503,'Industry classification is unavailable or invalid') from None


@router.get('/industries')
def industries(response:Response):
    response.headers['Cache-Control']='private, no-store'
    taxonomy=taxonomy_read()
    if taxonomy is None:
        return dict(contract='industry-directory-v1',status='UNAVAILABLE',taxonomy=None,industries=[])
    return dict(contract='industry-directory-v1',status='AVAILABLE',
        taxonomy=dict(name=taxonomy.name,version=taxonomy.version,source_reference=taxonomy.source_reference),
        industries=[i.model_dump() for i in taxonomy.industries])


@router.get('/industries/{industry_id}')
def industry_financials(industry_id:str,response:Response,
        period:str=Query(pattern=r'^\d{4}(?:-Q[1-4])?$'), membership_on:date=Query(),
        frequency:Literal['annual','quarterly','ttm']='annual',
        report_scope:Literal['consolidated','standalone']='consolidated',as_of:datetime|None=None):
    response.headers['Cache-Control']='private, no-store'
    if not 1900<=int(period[:4])<=2200 or (frequency=='annual') != ('-Q' not in period) or as_of and (as_of.tzinfo is None or as_of.utcoffset() is None):
        raise HTTPException(422,'Incompatible period or missing timezone')
    taxonomy=taxonomy_read()
    if taxonomy is None or not any(i.id==industry_id for i in taxonomy.industries):
        raise HTTPException(404,'Reviewed industry classification unavailable')
    journal=os.getenv('WOOFI_FINANCIAL_JOURNAL')
    observations=[]
    if journal:
        try:
            observations=MetricJournal(journal,readonly=True).read(as_of=as_of,period=period,frequency=frequency)
        except (ValueError,OSError,sqlite3.Error):
            raise HTTPException(503,'Financial journal is unavailable or invalid') from None
    return industry_snapshot(taxonomy,observations,industry_id,period=period,frequency=frequency,
        membership_on=membership_on,report_scope=report_scope)
