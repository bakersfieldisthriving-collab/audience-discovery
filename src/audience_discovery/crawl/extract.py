from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from audience_discovery.models import ExtractedSignals, PageContent, UNKNOWN


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SPONSOR_PATTERNS = {
    "media_kit": re.compile(r"\b(media kit|press kit)\b", re.IGNORECASE),
    "advertise": re.compile(r"\b(advertise|advertising|sponsor|sponsorship|partners?)\b", re.IGNORECASE),
}
CONTACT_FORM_RE = re.compile(r"\b(contact form|contact us|business inquir|partnership inquir)\b", re.IGNORECASE)
AUDIENCE_SIZE_RE = re.compile(
    r"\b(\d[\d,.]*\s*(?:k|m|million|thousand)?\s*(?:subscribers|members|readers|followers|listeners))\b",
    re.IGNORECASE,
)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.meta_description = UNKNOWN
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attrs_dict.get("name", "").lower() == "description":
            self.meta_description = attrs_dict.get("content", "").strip() or UNKNOWN
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(urljoin(self.base_url, attrs_dict["href"]))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text or self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(text)
        self.text_parts.append(text)


def parse_html(url: str, html: str) -> PageContent:
    parser = _HTMLTextExtractor(url)
    parser.feed(html)
    title = " ".join(parser.title_parts).strip() or UNKNOWN
    text = " ".join(parser.text_parts).strip() or UNKNOWN
    links = list(dict.fromkeys(parser.links))
    return PageContent(url=url, title=title, meta_description=parser.meta_description, text=text, links=links)


def detect_sponsor_signal(text: str, links: list[str] | None = None) -> str:
    combined = f"{text} {' '.join(links or [])}"
    if SPONSOR_PATTERNS["media_kit"].search(combined):
        return "media_kit"
    if SPONSOR_PATTERNS["advertise"].search(combined):
        return "advertise_or_sponsor"
    return "none"


def detect_platform(text: str, url: str = "", links: list[str] | None = None) -> str:
    combined = f"{url} {text} {' '.join(links or [])}".lower()
    if "youtube.com" in combined or "youtu.be" in combined or "youtube channel" in combined:
        return "youtube"
    if "discord" in combined:
        return "discord"
    if "skool.com" in combined or "skool" in combined:
        return "skool"
    if "reddit.com" in combined or "subreddit" in combined:
        return "reddit"
    if "podcast" in combined:
        return "podcast"
    if "newsletter" in combined or "substack" in combined or "beehiiv" in combined:
        return "newsletter"
    return "website"


def detect_contact(text: str, links: list[str] | None = None) -> tuple[str, str]:
    email_match = EMAIL_RE.search(text)
    if email_match:
        return "public_email", email_match.group(0)
    for link in links or []:
        lowered = link.lower()
        if lowered.startswith("mailto:"):
            return "public_email", link[7:].split("?")[0]
        if "contact" in lowered or "advertise" in lowered or "sponsor" in lowered:
            return "contact_form_or_page", link
    if CONTACT_FORM_RE.search(text):
        return "contact_form_or_page", UNKNOWN
    return UNKNOWN, UNKNOWN


def extract_audience_size(text: str) -> str:
    match = AUDIENCE_SIZE_RE.search(text)
    return match.group(1) if match else UNKNOWN


def extract_signals(page: PageContent) -> ExtractedSignals:
    text = " ".join([page.title, page.meta_description, page.text])
    contact_method, public_contact = detect_contact(text, page.links)
    return ExtractedSignals(
        sponsor_signal=detect_sponsor_signal(text, page.links),
        contact_method=contact_method,
        public_contact=public_contact,
        platform=detect_platform(text, page.url, page.links),
        audience_description=page.meta_description if page.meta_description != UNKNOWN else page.title,
        source_urls=[page.url],
    )
