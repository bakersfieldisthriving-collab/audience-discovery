from audience_discovery.models import Lead
from audience_discovery.storage.db import LeadStore


def test_upsert_dedupes_by_domain(tmp_path) -> None:
    store = LeadStore(tmp_path / "leads.sqlite")
    try:
        store.upsert_lead(
            Lead(
                entity_name="Example Prospect",
                url="https://www.example.com/sponsor",
                domain="www.example.com",
                audience_type="Biohacking",
                lead_type="Sponsor Page",
                sponsorship_probability=80,
                source_urls=["https://www.example.com/sponsor"],
            )
        )
        store.upsert_lead(
            Lead(
                entity_name="Different Page Title",
                url="https://example.com/advertise",
                domain="example.com",
                source_urls=["https://example.com/advertise"],
            )
        )

        leads = store.list_leads()

        assert len(leads) == 1
        assert set(leads[0].source_urls) == {
            "https://www.example.com/sponsor",
            "https://example.com/advertise",
        }
        assert leads[0].audience_type == "Biohacking"
        assert leads[0].lead_type == "Sponsor Page"
        assert leads[0].sponsorship_probability == 80
    finally:
        store.close()
