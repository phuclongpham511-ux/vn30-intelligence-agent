"""Frozen benchmark facade over the shared D4 lifecycle implementation."""
from src.analytics.episodes import link_episodes as _shared_link_episodes


def link_episodes(instrument, family, rows):
    # No prospective warm-up adaptation: existing benchmark outputs stay identical.
    return _shared_link_episodes(instrument, family, rows)
