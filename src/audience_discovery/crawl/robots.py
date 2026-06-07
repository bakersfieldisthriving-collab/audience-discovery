from __future__ import annotations

from functools import lru_cache
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests


@lru_cache(maxsize=256)
def _load_robot_parser(base_url: str, user_agent: str, timeout: float) -> RobotFileParser:
    parser = RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    parser.set_url(robots_url)
    try:
        response = requests.get(robots_url, timeout=timeout, headers={"User-Agent": user_agent})
        if response.status_code >= 400:
            parser.allow_all = True
        else:
            parser.parse(response.text.splitlines())
    except requests.RequestException:
        parser.allow_all = True
    return parser


def can_fetch(url: str, user_agent: str, timeout: float = 5.0) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    parser = _load_robot_parser(base_url, user_agent, timeout)
    return parser.can_fetch(user_agent, url)
