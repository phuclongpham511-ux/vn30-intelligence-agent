from fastapi import FastAPI
from routers import health, stocks, watchlists

app = FastAPI(title="VN30 Intelligence Agent", version="0.1.0")
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(watchlists.router)
