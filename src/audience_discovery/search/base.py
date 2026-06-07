from __future__ import annotations

from abc import ABC, abstractmethod

from audience_discovery.models import SearchResult


class SearchProvider(ABC):
    name = "base"

    @abstractmethod
    def search(self, query: str, category: str, limit: int = 10) -> list[SearchResult]:
        """Return public search results for a query."""
