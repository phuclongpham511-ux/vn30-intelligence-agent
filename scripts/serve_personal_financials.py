"""Loopback-only saved financial research API. No acquisition or persistent DB.

python -m scripts.serve_personal_financials PRIVATE_CAPTURE_DIRECTORY
Uses the one canonical main.app; public/source acquisition routes are denied.
"""
import os
from pathlib import Path
import sys

def run(directory):
    root = Path(directory).resolve(strict=True)
    if not (root / 'index.json').is_file():
        raise ValueError('Prepare hash-pinned saved captures first')
    os.environ.update(APP_ENV='development', DATABASE_URL='sqlite://',
        TECHNICAL_EOD_PILOT='false', WOOFI_PERSONAL_RESEARCH='1',
        WOOFI_PERSONAL_BIND='127.0.0.1', WOOFI_PERSONAL_CAPTURES=str(root),
        SSI_API_KEY='', SSI_API_SECRET='')
    from main import app
    from fastapi.responses import JSONResponse
    @app.middleware('http')
    async def research_only(request, call_next):
        if not request.url.path.startswith('/personal-research/'):
            return JSONResponse({'detail':'Not Found'},status_code=404)
        return await call_next(request)
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8432, proxy_headers=False)

if __name__ == '__main__':
    run(sys.argv[1])
