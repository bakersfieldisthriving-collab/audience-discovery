from __future__ import annotations

from hashlib import sha1

from audience_discovery.models import SearchResult
from audience_discovery.search.base import SearchProvider


class MockSearchProvider(SearchProvider):
    name = "mock"

    def search(self, query: str, category: str, limit: int = 10) -> list[SearchResult]:
        results: list[SearchResult] = []
        for index in range(max(0, limit)):
            token = sha1(f"{category}:{query}:{index}".encode("utf-8")).hexdigest()[:8]
            slug = query.lower().replace("'", "").replace(" ", "-")
            results.append(
                SearchResult(
                    title=f"{query.title()} Prospect {index + 1}",
                    url=f"https://example-{token}.com/{slug}",
                    snippet=(
                        f"Public sponsor and advertising page for {category}. "
                        "Business inquiries: sponsor@example.com."
                    ),
                    category=category,
                    source=self.name,
                )
            )
        return results
