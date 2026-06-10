from audience_discovery.ai.scoring import assess_compliance_risk, classify_audience_type, classify_lead_type, score_lead
from audience_discovery.models import Lead


WEIGHTS = {
    "audience_relevance": 30,
    "sponsorship_readiness": 20,
    "commercial_intent": 15,
    "trust_brand_safety": 15,
    "contactability": 10,
    "compliance_safety": 10,
}


def test_score_lead_rewards_ready_public_prospect() -> None:
    lead = Lead(
        entity_name="Longevity Newsletter",
        category="longevity_communities",
        platform="newsletter",
        url="https://longevity.example/advertise",
        audience_description="Longevity and healthspan newsletter",
        sponsor_signal="media_kit",
        contact_method="public_email",
        public_contact="ads@longevity.example",
        compliance_risk="low",
    )

    scored = score_lead(lead, WEIGHTS)

    assert scored.fit_score >= 60
    assert scored.audience_type == "Longevity"
    assert scored.lead_type == "Media Kit"
    assert scored.sponsorship_probability >= 70


def test_compliance_risk_flags_unsafe_claims() -> None:
    assert assess_compliance_risk("A miracle cure with before and after claims") == "high"


def test_lead_type_penalizes_directories_and_articles() -> None:
    directory = Lead(
        entity_name="The Best Longevity Newsletters",
        category="longevity_communities",
        platform="newsletter",
        url="https://directory.example/best-longevity-newsletters",
        audience_description="A curated roundup and directory of top longevity newsletters.",
        sponsor_signal="advertise_or_sponsor",
        contact_method="contact_form_or_page",
        public_contact="https://directory.example/advertise",
        compliance_risk="low",
    )
    operator = Lead(
        entity_name="Longevity Weekly Advertise",
        category="longevity_communities",
        platform="newsletter",
        url="https://longevityweekly.example/advertise",
        audience_description="Longevity Weekly newsletter sponsorship and advertising opportunities.",
        sponsor_signal="advertise_or_sponsor",
        contact_method="public_email",
        public_contact="ads@longevityweekly.example",
        compliance_risk="low",
    )

    scored_directory = score_lead(directory, WEIGHTS)
    scored_operator = score_lead(operator, WEIGHTS)

    assert classify_audience_type(directory) == "Longevity"
    assert classify_lead_type(directory) == "Newsletter"
    assert scored_operator.lead_type == "Sponsor Page"
    assert scored_operator.sponsorship_probability > scored_directory.sponsorship_probability
    assert scored_operator.fit_score > scored_directory.fit_score


def test_audience_type_classification_maps_requested_categories() -> None:
    assert classify_audience_type(Lead(category="biohacking_newsletters")) == "Biohacking"
    assert classify_audience_type(Lead(category="mens_health_adjacent_creators")) == "Men's Health"
    assert classify_audience_type(Lead(category="fitness_science_communities")) == "Fitness Science"
    assert classify_audience_type(Lead(category="nootropics_audiences")) == "Nootropics"
    assert classify_audience_type(Lead(category="lab_research_supply_audiences")) == "Lab/Research"
