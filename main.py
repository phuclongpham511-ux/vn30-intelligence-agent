from fastapi import FastAPI
from routers import health, stocks, watchlists
from fastapi import Request
from fastapi.responses import JSONResponse
from src.providers.base import ProviderError

app = FastAPI(title="VN30 Intelligence Agent", version="0.1.0")
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(watchlists.router)


@app.exception_handler(ProviderError)
async def provider_error(request: Request, exc: ProviderError):
    return JSONResponse(status_code=502, content={"detail": "Data provider is temporarily unavailable. Please retry later."})
