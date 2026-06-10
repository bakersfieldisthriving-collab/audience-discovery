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
LISTICLE_PATTERNS = re.compile(r"\b(best|top|list of|directory|collection|roundup|ranked|curated)\b", re.IGNORECASE)
AGGREGATOR_PATTERNS = re.compile(r"\b(inboxreads|marketplace|database|catalog|all newsletters)\b", re.IGNORECASE)
ARTICLE_PATTERNS = re.compile(r"\b(blog|article|guide|strategies|tips|how to|what is|news)\b", re.IGNORECASE)
MEDIA_KIT_PATTERNS = re.compile(r"\b(media kit|press kit)\b", re.IGNORECASE)
SPONSOR_PAGE_PATTERNS = re.compile(r"\b(sponsor|sponsorship|advertise|advertising|partnerships?)\b", re.IGNORECASE)
BUSINESS_INQUIRY_PATTERNS = re.compile(r"\b(business inquir|contact us|work with me|work with us)\b", re.IGNORECASE)
PRIOR_SPONSOR_PATTERNS = re.compile(r"\b(our sponsors|sponsored by|past sponsors|trusted by|brand partners)\b", re.IGNORECASE)

AUDIENCE_TYPE_RULES = [
    ("Biohacking", ("biohacking", "wearable", "optimization", "quantified self")),
    ("Longevity", ("longevity", "healthspan", "aging", "lifespan")),
    ("Men's Health", ("men's health", "testosterone", "hormone", "male health")),
    ("Fitness Science", ("fitness science", "evidence based fitness", "exercise science", "strength", "sports science")),
    ("Nootropics", ("nootropic", "cognitive", "focus", "brain")),
    ("Lab/Research", ("lab", "research", "biotech", "supplies", "scientific")),
]


def assess_compliance_risk(text: str) -> str:
    if HIGH_RISK_PATTERNS.search(text):
        return "high"
    if MEDIUM_RISK_PATTERNS.search(text):
        return "medium"
    return "low"


def classify_audience_type(lead: Lead) -> str:
    text = _lead_text(lead).lower()
    category = lead.category.lower()
    if "biohacking" in category:
        return "Biohacking"
    if "longevity" in category:
        return "Longevity"
    if "mens_health" in category or "men's health" in text:
        return "Men's Health"
    if "fitness" in category:
        return "Fitness Science"
    if "nootropics" in category:
        return "Nootropics"
    if "lab" in category or "research" in category:
        return "Lab/Research"
    for audience_type, keywords in AUDIENCE_TYPE_RULES:
        if any(keyword in text for keyword in keywords):
            return audience_type
    return "unknown"


def classify_lead_type(lead: Lead) -> str:
    text = _lead_text(lead)
    lowered_url = lead.url.lower()
    if MEDIA_KIT_PATTERNS.search(text) or lead.sponsor_signal == "media_kit":
        return "Media Kit"
    if SPONSOR_PAGE_PATTERNS.search(text) and any(term in lowered_url for term in ("sponsor", "advertise", "media-kit", "media_kit", "partners")):
        return "Sponsor Page"
    if lead.platform == "podcast" or "podcast" in text.lower():
        return "Podcast"
    if lead.platform in {"discord", "skool", "reddit"} or "community" in text.lower():
        return "Community"
    if lead.platform == "newsletter" or "newsletter" in text.lower():
        return "Newsletter"
    if lead.platform == "youtube" or any(term in text.lower() for term in ("creator", "youtube", "channel", "subscribers")):
        return "Creator"
    return "Creator" if lead.public_contact != "unknown" else "unknown"


def is_low_quality_surface(lead: Lead) -> bool:
    text = _lead_text(lead)
    lowered_url = lead.url.lower()
    return (
        bool(LISTICLE_PATTERNS.search(text))
        or bool(AGGREGATOR_PATTERNS.search(text))
        or bool(ARTICLE_PATTERNS.search(text))
        or "/blog/" in lowered_url
    )


def calculate_sponsorship_probability(lead: Lead) -> int:
    text = _lead_text(lead)
    lowered = text.lower()
    probability = 0
    if lead.sponsor_signal == "media_kit" or MEDIA_KIT_PATTERNS.search(text):
        probability += 30
    if "advertise" in lowered or "advertising" in lowered:
        probability += 20
    if "sponsor" in lowered or "sponsorship" in lowered:
        probability += 20
    if BUSINESS_INQUIRY_PATTERNS.search(text):
        probability += 10
    if PRIOR_SPONSOR_PATTERNS.search(text):
        probability += 10
    if lead.lead_type == "Newsletter":
        probability += 15
    if lead.lead_type == "Creator":
        probability += 12
    if lead.lead_type == "Podcast":
        probability += 14
    if lead.lead_type in {"Media Kit", "Sponsor Page"}:
        probability += 20
    if lead.contact_method in {"public_email", "contact_form_or_page"} and lead.public_contact != "unknown":
        probability += 10
    if is_low_quality_surface(lead):
        probability -= 25
    if lead.compliance_risk == "high":
        probability -= 30
    return max(0, min(100, probability))


def _lead_text(lead: Lead) -> str:
    return " ".join(
        [
            lead.entity_name,
            lead.category,
            lead.audience_type,
            lead.platform,
            lead.url,
            lead.domain,
            lead.audience_description,
            lead.sponsor_signal,
            lead.contact_method,
            lead.public_contact,
            lead.fit_reason,
        ]
    )


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
    if lead.audience_type == "unknown":
        lead.audience_type = classify_audience_type(lead)
    if lead.lead_type == "unknown":
        lead.lead_type = classify_lead_type(lead)
    text = _lead_text(lead)
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

    if lead.lead_type in {"Media Kit", "Sponsor Page"}:
        score += 15
    elif lead.lead_type in {"Newsletter", "Creator", "Podcast", "Community"}:
        score += 8
    if is_low_quality_surface(lead):
        score -= 20

    lead.fit_score = max(0, min(100, score))
    lead.sponsorship_probability = calculate_sponsorship_probability(lead)
    if lead.fit_reason == "unknown":
        lead.fit_reason = (
            "Local deterministic score based on relevance, lead type, sponsor signal, "
            "contactability, sponsorship probability, and compliance risk."
        )
    return lead
