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
    finally:
        store.close()
