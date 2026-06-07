from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

import requests

from audience_discovery.crawl.extract import parse_html
from audience_discovery.crawl.robots import can_fetch
from audience_discovery.models import PageContent, UNKNOWN


USER_AGENT = "AudienceDiscoveryMVP/0.1 (+public compliance research; no outreach automation)"


class HttpClient(Protocol):
    def get(self, url: str, timeout: float, headers: dict[str, str]) -> requests.Response:
        ...


@dataclass
class FetchResult:
    ok: bool
    page: PageContent
    error: str = ""


class PageFetcher:
    def __init__(
        self,
        client: HttpClient | None = None,
        user_agent: str = USER_AGENT,
        timeout: float = 10.0,
        rate_limit_seconds: float = 1.0,
        respect_robots: bool = True,
    ) -> None:
        self.client = client or requests.Session()
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit_seconds = rate_limit_seconds
        self.respect_robots = respect_robots
        self._last_fetch_at = 0.0

    def fetch(self, url: str) -> FetchResult:
        if self.respect_robots and not can_fetch(url, self.user_agent):
            return FetchResult(False, PageContent(url=url), "Blocked by robots.txt")
        elapsed = time.monotonic() - self._last_fetch_at
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        try:
            response = self.client.get(url, timeout=self.timeout, headers={"User-Agent": self.user_agent})
            self._last_fetch_at = time.monotonic()
            response.raise_for_status()
        except requests.RequestException as exc:
            return FetchResult(False, PageContent(url=url), str(exc))

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower() and response.text.strip().startswith("<") is False:
            return FetchResult(False, PageContent(url=url, text=UNKNOWN), "Response did not look like HTML")
        return FetchResult(True, parse_html(url, response.text))
