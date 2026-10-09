from fastapi import FastAPI
from routers import health, stocks, watchlists, news, community, ingestion, technical
from fastapi import Request
from fastapi.responses import JSONResponse
from src.providers.base import ProviderError
from contextlib import asynccontextmanager
from src.config.settings import get_settings
from src.db.session import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local first-run setup only; production schema deployment stays explicit.
    if get_settings().app_env == "development":
        create_tables()
    try:
        yield
    finally:
        from src.services.live_market import close_live_market
        close_live_market()


app = FastAPI(title="VN30 Intelligence Agent", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(watchlists.router)
app.include_router(news.router)
app.include_router(community.router)
app.include_router(ingestion.router)
app.include_router(technical.router)


@app.exception_handler(ProviderError)
async def provider_error(request: Request, exc: ProviderError):
    return JSONResponse(status_code=502, content={"detail": "Data provider is temporarily unavailable. Please retry later."})
