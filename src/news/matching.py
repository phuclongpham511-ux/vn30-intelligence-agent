from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from src.news.models import NewsStory
from src.news.normalization import normalized, utc
from src.news.tagging import Tags

STOP = {'the', 'a', 'an', 'and', 'of', 'to', 'in', 'for', 'on', 'with', 'va', 'cua', 'cho', 'tai', 'voi', 'la', 'trong', 'cac', 'nhung', 've'}


def tokens(title: str) -> set[str]:
    return set(normalized(title).split()) - STOP


class StoryMatcher(Protocol):
    def match(self, title: str, tags: Tags, stories: list[NewsStory], now: datetime) -> NewsStory | None: ...


@dataclass
class LexicalStoryMatcher:
    window_hours: int = 72
    similarity_threshold: float = 0.64
    lexical_floor: float = 0.50

    def match(self, title, tags, stories, now):
        best, best_score = None, self.similarity_threshold
        left = tokens(title)
        for story in sorted(stories, key=lambda s: s.id):
            if utc(story.first_seen_at) < utc(now) - timedelta(hours=self.window_hours):
                continue
            right = tokens(story.representative_title)
            # Conflicting numbers often indicate different earnings periods or events.
            ln = {x for x in left if x.isdigit()}
            rn = {x for x in right if x.isdigit()}
            if ln and rn and ln != rn:
                continue
            lexical = len(left & right) / max(1, len(left | right))
            overlap = bool(set(tags.topics) & set(story.topics) or set(tags.tickers) & set(story.tickers))
            score = lexical + (0.12 if overlap else 0)
            if lexical >= self.lexical_floor and score >= best_score:
                best, best_score = story, score
        return best
