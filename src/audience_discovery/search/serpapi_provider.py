from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

import requests

from audience_discovery.models import SearchResult, domain_from_url, normalize_domain
from audience_discovery.search.base import SearchProvider


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


class SerpAPIClient(Protocol):
    def get(self, url: str, params: dict[str, Any], timeout: float) -> requests.Response:
        ...


@dataclass
class SerpAPIProvider(SearchProvider):
    api_key: str | None = None
    client: SerpAPIClient | None = None
    page_size: int = 10
    timeout: float = 10.0
    rate_limit_seconds: float = 1.0
    max_retries: int = 2

    name = "serpapi"

    def __post_init__(self) -> None:
        self.api_key = self.api_key if self.api_key is not None else os.getenv("SERPAPI_API_KEY")
        self.client = self.client or requests.Session()
        self.warning: str | None = None
        self._last_request_at = 0.0

    def search(self, query: str, category: str, limit: int = 10) -> list[SearchResult]:
        if not self.api_key:
            self.warning = "SERPAPI_API_KEY is not configured; SerpAPIProvider returned no results."
            return []

        results: list[SearchResult] = []
        seen_urls: set[str] = set()
        seen_domains: set[str] = set()
        start = 0

        while len(results) < limit:
            page_limit = min(self.page_size, limit - len(results))
            payload = self._request_page(query=query, start=start, num=page_limit)
            organic_results = payload.get("organic_results", [])
            if not organic_results:
                break

            added_this_page = 0
            for item in organic_results:
                url = str(item.get("link") or item.get("url") or "").strip()
                if not url:
                    continue
                domain = normalize_domain(domain_from_url(url))
                normalized_url = url.rstrip("/")
                if normalized_url in seen_urls or domain in seen_domains:
                    continue
                seen_urls.add(normalized_url)
                seen_domains.add(domain)
                results.append(
                    SearchResult(
                        title=str(item.get("title") or "unknown"),
                        url=url,
                        snippet=str(item.get("snippet") or item.get("rich_snippet", {}).get("top", {}).get("detected_extensions", {}) or "unknown"),
                        category=category,
                        domain=domain,
                        source=self.name,
                    )
                )
                added_this_page += 1
                if len(results) >= limit:
                    break

            if len(organic_results) < page_limit:
                break
            start += self.page_size
            if added_this_page == 0 and start >= limit + self.page_size:
                break

        return results

    def _request_page(self, query: str, start: int, num: int) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._wait_for_rate_limit()
            try:
                response = self.client.get(
                    SERPAPI_ENDPOINT,
                    params={
                        "engine": "google",
                        "q": query,
                        "api_key": self.api_key,
                        "num": num,
                        "start": start,
                    },
                    timeout=self.timeout,
                )
                self._last_request_at = time.monotonic()
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    return {}
                return data
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                self.warning = f"SerpAPI request failed: {last_error}"
                return {}
        return {}

    def _wait_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
