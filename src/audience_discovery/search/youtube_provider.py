from __future__ import annotations

import os

from audience_discovery.models import SearchResult
from audience_discovery.search.base import SearchProvider


class YouTubeProvider(SearchProvider):
    name = "youtube"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("YOUTUBE_API_KEY")
        self.warning: str | None = None

    def search(self, query: str, category: str, limit: int = 10) -> list[SearchResult]:
        if not self.api_key:
            self.warning = "YOUTUBE_API_KEY is not configured; YouTubeProvider returned no results."
            return []
        self.warning = (
            "YouTubeProvider is configured but API search is not implemented in this MVP; "
            "no YouTube HTML scraping is performed."
        )
        return []
