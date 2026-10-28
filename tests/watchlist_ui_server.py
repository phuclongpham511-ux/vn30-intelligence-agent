"""Isolated synthetic browser-validation API. Never reads operator databases."""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))

from sqlalchemy.pool import StaticPool
from sqlmodel import Session,create_engine
from main import app
from src.config.settings import get_settings
from src.db.session import create_tables,get_session
from src.models import Stock
from src.community.models import CommunityEvidenceItem
from src.news.models import NewsSourceState
from src.news.registry import load_sources
from src.news.service import ingest_cycle
from src.news.adapters import ArticleInput
from test_technical_eod_persistence import setup,run


def serve():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    create_tables(engine)
    now=datetime.now(timezone.utc)
    with Session(engine) as session:
        *_,second,accepted_at=setup(session)
        run(session,second,accepted_at)
        session.add(Stock(symbol='XYZ',company_name='Synthetic browser test issuer',display_name_en='Synthetic browser test issuer',exchange='HOSE'))
        session.add(Stock(symbol='EMPTY',company_name='Synthetic empty issuer',exchange='HOSE'))
        session.commit()
        source=next(s for s in load_sources() if s.enabled and s.country=='VN')
        source=source.model_copy(update={'name':'Synthetic browser test source'})
        incoming=[ArticleInput('XYZ reports synthetic browser test results','https://example.org/watchlist-fixture',now)]
        ingest_cycle(session,[source],now=now,force=True,fetch=lambda _:incoming)
        session.add(CommunityEvidenceItem(id='chungsy_public:ui-fixture',source_id='chungsy_public',source_item_id='ui-fixture',item_type='post',
            title='Synthetic browser test discussion',excerpt='Synthetic browser test only: XYZ discussion evidence, no sentiment inference.',
            url='https://example.org/community-fixture',published_at=now-timedelta(minutes=1),
            first_seen_at=now-timedelta(minutes=1),last_seen_at=now,tickers=['XYZ'],revision_id='synthetic-v1',is_fixture=True))
        session.commit()
    def db():
        with Session(engine) as session:yield session
    app.dependency_overrides[get_session]=db
    get_settings().app_env='production'
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8122)


if __name__=='__main__':serve()
