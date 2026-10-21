"""Default-off, socket-verified loopback access; no provider or database calls."""
import os
from fastapi import APIRouter, HTTPException, Request, Query, Path, Depends
from typing import Literal
from src.services.personal_financials import saved_research_packet, personal_projection

def require_personal_request(request: Request):
    if (os.getenv('WOOFI_PERSONAL_RESEARCH') != '1' or os.getenv('APP_ENV') != 'development'
        or os.getenv('WOOFI_PERSONAL_BIND') != '127.0.0.1'
        or not request.client or request.client.host != '127.0.0.1'
        or request.url.hostname != '127.0.0.1'):
        raise HTTPException(404)


router = APIRouter(prefix='/personal-research', include_in_schema=False,
    dependencies=[Depends(require_personal_request)])


@router.get('/financials/{symbol}')
def financials(request: Request, symbol: str = Path(pattern=r'^[A-Z0-9]{1,20}$'),
               frequency: Literal['annual','quarterly','ttm'] = 'annual', limit: int = Query(34, ge=1, le=40),
               evidence: Literal['preferred','provider'] = 'preferred'):
    # request.client is the ASGI socket peer, not X-Forwarded-For. The supported
    # launcher disables proxy_headers and binds only the numeric loopback host.
    try:
        packet, digest = saved_research_packet(os.environ['WOOFI_PERSONAL_CAPTURES'], symbol,
            frequency=frequency, evidence=evidence)
        result = personal_projection(packet, frequency=frequency, limit=limit,
            authorization_reference='task:financial-v6-personal-research:' + digest)
        if packet.source.startswith('issuer:'):
            from src.services.personal_financials import saved_packet
            from src.analytics.financial_engine import financial_engine
            try:
                provider,_ = saved_packet(os.environ['WOOFI_PERSONAL_CAPTURES'], symbol)
                result['available_period_types'] = sorted(set(result['available_period_types']) |
                    set(financial_engine(provider,limit=1).available_period_types))
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        raise HTTPException(404, 'Saved personal financial coverage unavailable') from None
    except (ValueError, KeyError, TypeError, OSError):
        raise HTTPException(503, 'Saved personal evidence invalid or unavailable') from None
    from fastapi.responses import JSONResponse
    return JSONResponse(result, headers={'Cache-Control':'private, no-store', 'X-Robots-Tag':'noindex, nofollow'})


@router.get('/industries')
def industries():
    from src.services.observed_industries import observed_directory
    return private_read(lambda: observed_directory(os.environ['WOOFI_PERSONAL_CAPTURES']))


@router.get('/industries/{code}')
def industry(code: str = Path(pattern=r'^\d{1,16}$'), period: str = Query(pattern=r'^\d{4}(?:-Q[1-4])?$'),
             frequency: Literal['annual','quarterly','ttm']='annual'):
    from src.services.observed_industries import observed_peers
    return private_read(lambda: observed_peers(os.environ['WOOFI_PERSONAL_CAPTURES'],code,period=period,frequency=frequency))


def private_read(read):
    from fastapi.responses import JSONResponse
    try:
        return JSONResponse(read(),headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'})
    except (FileNotFoundError,KeyError):
        raise HTTPException(404,'Saved research coverage unavailable') from None
    except (ValueError,TypeError,OSError):
        raise HTTPException(503,'Saved research evidence invalid or unavailable') from None


@router.get('/dividends/{symbol}')
def dividends(symbol: str = Path(pattern=r'^[A-Z0-9]{1,20}$')):
    def read():
        import json
        from pathlib import Path as FilePath
        from src.providers.reviewed_reports import pinned_file
        from src.providers.vsdc_dividends import dividend_page
        root=FilePath(os.environ['WOOFI_PERSONAL_CAPTURES']).resolve(strict=True)
        if (root/'index.json').stat().st_size>2_000_000:raise ValueError('Oversized evidence index')
        index=json.loads((root/'index.json').read_text(encoding='utf-8'))
        entry=index['dividends']
        return dividend_page(json.loads(pinned_file(root,entry['file'],entry['sha256'],4_000_000)),symbol)
    return private_read(read)


@router.get('/peers/{symbol}')
def peers(symbol: str = Path(pattern=r'^[A-Z0-9]{1,20}$'),
          period: str = Query(pattern=r'^\d{4}(?:-Q[1-4])?$'),
          frequency: Literal['annual','quarterly','ttm']='annual'):
    from src.services.observed_industries import company_peers
    return private_read(lambda: company_peers(os.environ['WOOFI_PERSONAL_CAPTURES'],symbol,period=period,frequency=frequency))
