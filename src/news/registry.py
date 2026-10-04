import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class Source(BaseModel):
    source_id: str
    name: str
    country: str
    language: str
    method: Literal['RSS', 'API', 'HTML'] = 'RSS'
    endpoint: HttpUrl
    enabled: bool = True
    poll_interval_minutes: int = Field(default=20, ge=15, le=1440)
    category: Literal['VN', 'GLOBAL']
    publisher_group: str
    # Naive publisher dates are interpreted in the publisher's timezone.
    timezone: str = 'UTC'
    verified_at: str | None = None


def load_sources(path: str | None = None) -> list[Source]:
    """Reload operator-controlled JSON each cycle; no deployment needed to toggle feeds."""
    file = Path(path) if path else Path(__file__).with_name('sources.json')
    sources = [Source.model_validate(row) for row in json.loads(file.read_text())]
    if len({s.source_id for s in sources}) != len(sources):
        raise ValueError('Duplicate source_id')
    return sources
