from __future__ import annotations

import json
import os
from typing import Any

from audience_discovery.ai.scoring import assess_compliance_risk, score_lead
from audience_discovery.crawl.extract import extract_audience_size, extract_signals
from audience_discovery.models import Lead, PageContent, SearchResult, domain_from_url


STRUCTURED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entity_name": {"type": "string"},
        "category": {"type": "string"},
        "platform": {"type": "string"},
        "url": {"type": "string"},
        "audience_type": {"type": "string"},
        "audience_description": {"type": "string"},
        "audience_size_estimate": {"type": "string"},
        "lead_type": {"type": "string"},
        "sponsor_signal": {"type": "string"},
        "contact_method": {"type": "string"},
        "public_contact": {"type": "string"},
        "fit_score": {"type": "integer"},
        "sponsorship_probability": {"type": "integer"},
        "compliance_risk": {"type": "string"},
        "fit_reason": {"type": "string"},
        "outreach_angle": {"type": "string"},
        "source_urls": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "entity_name",
        "category",
        "platform",
        "url",
        "audience_type",
        "audience_description",
        "audience_size_estimate",
        "lead_type",
        "sponsor_signal",
        "contact_method",
        "public_contact",
        "fit_score",
        "sponsorship_probability",
        "compliance_risk",
        "fit_reason",
        "outreach_angle",
        "source_urls",
    ],
    "additionalProperties": False,
}


class LeadClassifier:
    def __init__(self, scoring_weights: dict[str, int], openai_api_key: str | None = None) -> None:
        self.scoring_weights = scoring_weights
        self.openai_api_key = openai_api_key if openai_api_key is not None else os.getenv("OPENAI_API_KEY")
        self.warning: str | None = None

    def classify(self, result: SearchResult, page: PageContent | None = None) -> Lead:
        if self.openai_api_key:
            lead = self._classify_with_openai(result, page)
        else:
            self.warning = "OPENAI_API_KEY is not configured; using deterministic local classification."
            lead = self._classify_locally(result, page)
        return score_lead(lead, self.scoring_weights)

    def _classify_with_openai(self, result: SearchResult, page: PageContent | None = None) -> Lead:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            self.warning = "OpenAI package is not installed; using deterministic local classification."
            return self._classify_locally(result, page)

        prompt_payload = {
            "search_result": result.__dict__,
            "page": page.__dict__ if page else None,
            "rules": [
                "Use unknown for missing values.",
                "Do not invent missing information.",
                "Only include public sponsor, advertise, media-kit, contact, or business information.",
                "Classify audience_type as Biohacking, Longevity, Men's Health, Fitness Science, Nootropics, Lab/Research, or unknown.",
                "Classify lead_type as Newsletter, Creator, Podcast, Community, Media Kit, Sponsor Page, or unknown.",
                "Score sponsorship_probability 0-100 based on media kit, advertise page, sponsor page, business inquiries, prior sponsors, newsletter ownership, and creator ownership.",
                "Flag high compliance risk for aggressive medical claims, minors, illegal drug sourcing, misleading before/after claims, or unsafe paid health-adjacent promotion.",
            ],
        }
        try:
            client = OpenAI(api_key=self.openai_api_key)
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                input=[
                    {
                        "role": "system",
                        "content": "Classify public sponsorship-ready audience prospects as strict JSON.",
                    },
                    {"role": "user", "content": json.dumps(prompt_payload)},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "lead_classification",
                        "schema": STRUCTURED_OUTPUT_SCHEMA,
                        "strict": True,
                    }
                },
            )
            parsed = json.loads(response.output_text)
            parsed["domain"] = domain_from_url(parsed.get("url", result.url))
            return Lead(**parsed)
        except Exception as exc:  # pragma: no cover - external API fallback path
            self.warning = f"OpenAI classification failed; using deterministic local fallback: {exc}"
            return self._classify_locally(result, page)

    def _classify_locally(self, result: SearchResult, page: PageContent | None = None) -> Lead:
        if page:
            signals = extract_signals(page)
            text = " ".join([page.title, page.meta_description, page.text, result.snippet])
            entity_name = page.title if page.title != "unknown" else result.title
            url = page.url
        else:
            pseudo_page = PageContent(
                url=result.url,
                title=result.title,
                meta_description=result.snippet,
                text=result.snippet,
                links=[],
            )
            signals = extract_signals(pseudo_page)
            text = " ".join([result.title, result.snippet])
            entity_name = result.title
            url = result.url

        compliance_risk = assess_compliance_risk(text)
        return Lead(
            entity_name=entity_name,
            category=result.category,
            platform=signals.platform,
            url=url,
            domain=domain_from_url(url),
            audience_type="unknown",
            audience_description=signals.audience_description,
            audience_size_estimate=extract_audience_size(text),
            lead_type="unknown",
            sponsor_signal=signals.sponsor_signal,
            contact_method=signals.contact_method,
            public_contact=signals.public_contact,
            fit_score=0,
            sponsorship_probability=0,
            compliance_risk=compliance_risk,
            fit_reason="unknown",
            outreach_angle="unknown",
            source_urls=signals.source_urls or [url],
        )
