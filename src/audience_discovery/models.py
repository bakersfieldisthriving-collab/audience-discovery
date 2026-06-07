from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


UNKNOWN = "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def unknown_if_blank(value: Any) -> str:
    if value is None:
        return UNKNOWN
    text = str(value).strip()
    return text if text else UNKNOWN


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or UNKNOWN


def normalize_domain(domain: str) -> str:
    normalized = unknown_if_blank(domain).lower()
    return normalized[4:] if normalized.startswith("www.") else normalized


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = UNKNOWN
    category: str = UNKNOWN
    source: str = "search"


@dataclass
class PageContent:
    url: str
    title: str = UNKNOWN
    meta_description: str = UNKNOWN
    text: str = UNKNOWN
    links: list[str] = field(default_factory=list)


@dataclass
class ExtractedSignals:
    sponsor_signal: str = "none"
    contact_method: str = UNKNOWN
    public_contact: str = UNKNOWN
    platform: str = UNKNOWN
    audience_description: str = UNKNOWN
    source_urls: list[str] = field(default_factory=list)


@dataclass
class Lead:
    entity_name: str = UNKNOWN
    category: str = UNKNOWN
    platform: str = UNKNOWN
    url: str = UNKNOWN
    domain: str = UNKNOWN
    audience_description: str = UNKNOWN
    audience_size_estimate: str = UNKNOWN
    sponsor_signal: str = "none"
    contact_method: str = UNKNOWN
    public_contact: str = UNKNOWN
    fit_score: int = 0
    compliance_risk: str = UNKNOWN
    fit_reason: str = UNKNOWN
    outreach_angle: str = UNKNOWN
    source_urls: list[str] = field(default_factory=list)
    status: str = "new"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        for field_name in (
            "entity_name",
            "category",
            "platform",
            "url",
            "domain",
            "audience_description",
            "audience_size_estimate",
            "sponsor_signal",
            "contact_method",
            "public_contact",
            "compliance_risk",
            "fit_reason",
            "outreach_angle",
            "status",
        ):
            setattr(self, field_name, unknown_if_blank(getattr(self, field_name)))
        if self.domain == UNKNOWN and self.url != UNKNOWN:
            self.domain = domain_from_url(self.url)
        self.domain = normalize_domain(self.domain)
        self.fit_score = max(0, min(100, int(self.fit_score or 0)))
        self.source_urls = [url for url in self.source_urls if unknown_if_blank(url) != UNKNOWN]
        if not self.source_urls and self.url != UNKNOWN:
            self.source_urls = [self.url]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_urls"] = ";".join(self.source_urls)
        return data

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Lead":
        data = {field: row[field] for field in LEAD_FIELDS if field in row}
        source_urls = data.get("source_urls") or ""
        if isinstance(source_urls, str):
            data["source_urls"] = [url for url in source_urls.split(";") if url]
        return cls(**data)


LEAD_FIELDS = [
    "entity_name",
    "category",
    "platform",
    "url",
    "domain",
    "audience_description",
    "audience_size_estimate",
    "sponsor_signal",
    "contact_method",
    "public_contact",
    "fit_score",
    "compliance_risk",
    "fit_reason",
    "outreach_angle",
    "source_urls",
    "status",
    "created_at",
    "updated_at",
]
