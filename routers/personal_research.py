"""Default-off, socket-verified loopback access; no provider or database calls."""
import os
from fastapi import APIRouter, HTTPException, Request, Query, Path
from typing import Literal
from src.services.personal_financials import saved_packet, personal_projection

router = APIRouter(prefix='/personal-research', include_in_schema=False)


@router.get('/financials/{symbol}')
def financials(request: Request, symbol: str = Path(pattern=r'^[A-Z0-9]{1,20}$'),
               frequency: Literal['annual','quarterly','ttm'] = 'annual', limit: int = Query(8, ge=1, le=20)):
    # request.client is the ASGI socket peer, not X-Forwarded-For. The supported
    # launcher disables proxy_headers and binds only the numeric loopback host.
    if (os.getenv('WOOFI_PERSONAL_RESEARCH') != '1' or os.getenv('APP_ENV') != 'development'
        or os.getenv('WOOFI_PERSONAL_BIND') != '127.0.0.1'
        or not request.client or request.client.host != '127.0.0.1'
        or request.url.hostname != '127.0.0.1'):
        raise HTTPException(404)
    try:
        packet, digest = saved_packet(os.environ['WOOFI_PERSONAL_CAPTURES'], symbol)
        result = personal_projection(packet, frequency=frequency, limit=limit,
            authorization_reference='task:financial-v6-personal-research:' + digest)
    except FileNotFoundError:
        raise HTTPException(404, 'Saved personal financial coverage unavailable') from None
    except (ValueError, KeyError, TypeError, OSError):
        raise HTTPException(503, 'Saved personal evidence invalid or unavailable') from None
    from fastapi.responses import JSONResponse
    return JSONResponse(result, headers={'Cache-Control':'private, no-store', 'X-Robots-Tag':'noindex, nofollow'})
