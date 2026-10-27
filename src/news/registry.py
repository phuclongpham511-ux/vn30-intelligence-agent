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
    representative_priority: int = Field(default=100, ge=0)
    scheduling_priority: Literal['priority', 'standard'] | None = None


def load_sources(path: str | None = None) -> list[Source]:
    """Reload operator-controlled JSON each cycle; no deployment needed to toggle feeds."""
    file = Path(path) if path else Path(__file__).with_name('sources.json')
    sources = [Source.model_validate(row) for row in json.loads(file.read_text(encoding='utf-8'))]
    if len({s.source_id for s in sources}) != len(sources):
        raise ValueError('Duplicate source_id')
    return sources


class CompanyAliases(BaseModel):
    symbol: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    aliases: list[str] = Field(min_length=1)
    source_url: HttpUrl
    verified_at: str


def load_company_aliases() -> dict[str, list[str]]:
    """Reviewed issuer identities, admitted only for members of the live universe."""
    rows = [CompanyAliases.model_validate(row) for row in json.loads(
        Path(__file__).with_name('company_aliases.json').read_text(encoding='utf-8'))]
    if len({row.symbol for row in rows}) != len(rows):
        raise ValueError('Duplicate alias issuer')
    return {row.symbol: [name.strip() for name in row.aliases if len(name.strip()) >= 3] for row in rows}
