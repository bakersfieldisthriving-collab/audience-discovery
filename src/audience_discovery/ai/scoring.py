from __future__ import annotations

import re

from audience_discovery.models import Lead


RELEVANCE_KEYWORDS = {
    "biohacking": {"biohacking", "wearable", "optimization", "healthspan"},
    "longevity": {"longevity", "healthspan", "aging", "lifespan"},
    "nootropics": {"nootropic", "cognitive", "focus", "brain"},
    "lab": {"lab", "biotech", "research", "supplies", "scientific"},
    "mens": {"men's health", "testosterone", "hormone", "performance"},
    "fitness": {"fitness", "exercise", "strength", "evidence based", "sports science"},
    "youtube": {"youtube", "channel", "subscribers"},
    "discord": {"discord", "community", "members"},
}


HIGH_RISK_PATTERNS = re.compile(
    r"\b(illegal drug|buy steroids|steroid source|miracle cure|guaranteed cure|targets minors|teen only|"
    r"before and after|medical miracle|cure cancer)\b",
    re.IGNORECASE,
)
MEDIUM_RISK_PATTERNS = re.compile(
    r"\b(testosterone|hormone|medical advice|supplement protocol|bioidentical|prescription)\b",
    re.IGNORECASE,
)


def assess_compliance_risk(text: str) -> str:
    if HIGH_RISK_PATTERNS.search(text):
        return "high"
    if MEDIUM_RISK_PATTERNS.search(text):
        return "medium"
    return "low"


def _category_keyword_score(category: str, text: str, max_points: int) -> int:
    lowered_category = category.lower()
    lowered_text = text.lower()
    matched = 0
    considered = 0
    for category_key, keywords in RELEVANCE_KEYWORDS.items():
        if category_key in lowered_category:
            considered += len(keywords)
            matched += sum(1 for keyword in keywords if keyword in lowered_text)
    if considered == 0:
        matched = sum(1 for keywords in RELEVANCE_KEYWORDS.values() for keyword in keywords if keyword in lowered_text)
        considered = 8
    return min(max_points, round(max_points * min(1.0, matched / max(1, min(considered, 4)))))


def score_lead(lead: Lead, weights: dict[str, int]) -> Lead:
    text = " ".join(
        [
            lead.entity_name,
            lead.category,
            lead.platform,
            lead.audience_description,
            lead.sponsor_signal,
            lead.contact_method,
            lead.public_contact,
            lead.fit_reason,
        ]
    )
    score = 0
    score += _category_keyword_score(lead.category, text, weights.get("audience_relevance", 30))
    if lead.sponsor_signal in {"media_kit", "advertise_or_sponsor"}:
        score += weights.get("sponsorship_readiness", 20)
    if any(term in text.lower() for term in ("sponsor", "advertise", "media kit", "business inquiries", "partnership")):
        score += weights.get("commercial_intent", 15)
    if lead.compliance_risk == "low":
        score += weights.get("trust_brand_safety", 15)
        score += weights.get("compliance_safety", 10)
    elif lead.compliance_risk == "medium":
        score += max(0, weights.get("trust_brand_safety", 15) // 2)
    else:
        score -= 25
    if lead.contact_method in {"public_email", "contact_form_or_page"} and lead.public_contact != "unknown":
        score += weights.get("contactability", 10)
    elif lead.contact_method == "contact_form_or_page":
        score += max(1, weights.get("contactability", 10) // 2)

    lead.fit_score = max(0, min(100, score))
    if lead.fit_reason == "unknown":
        lead.fit_reason = "Local deterministic score based on relevance, sponsor signal, contactability, and compliance risk."
    return lead
