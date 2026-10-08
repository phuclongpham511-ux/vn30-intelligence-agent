from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.services.ingestion import request_refresh


router = APIRouter(prefix='/ingestion', tags=['ingestion'])


class RefreshResponse(BaseModel):
    status: str


@router.post('/refresh', response_model=RefreshResponse)
def refresh():
    status = request_refresh()
    return JSONResponse(status_code=202 if status == 'started' else 200,
        content=RefreshResponse(status=status).model_dump())
