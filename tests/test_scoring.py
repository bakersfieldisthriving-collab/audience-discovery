from audience_discovery.ai.scoring import assess_compliance_risk, score_lead
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


def test_compliance_risk_flags_unsafe_claims() -> None:
    assert assess_compliance_risk("A miracle cure with before and after claims") == "high"
