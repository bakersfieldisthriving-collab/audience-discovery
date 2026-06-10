import csv

from audience_discovery.export.csv_exporter import CSVExporter
from audience_discovery.models import Lead


def test_csv_export_outputs_review_queue(tmp_path) -> None:
    leads = [
        Lead(
            entity_name="Ready",
            url="https://ready.example",
            fit_score=75,
            sponsorship_probability=65,
            audience_type="Longevity",
            lead_type="Sponsor Page",
            compliance_risk="low",
            sponsor_signal="advertise_or_sponsor",
            source_urls=["https://ready.example"],
        ),
        Lead(
            entity_name="Risky",
            url="https://risky.example",
            fit_score=90,
            sponsorship_probability=95,
            audience_type="Longevity",
            lead_type="Sponsor Page",
            compliance_risk="high",
            sponsor_signal="media_kit",
            source_urls=["https://risky.example"],
        ),
    ]

    counts = CSVExporter(tmp_path).export_all(leads)

    assert counts == {"raw": 2, "scored": 2, "review_queue": 1}
    with (tmp_path / "leads_review_queue.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["entity_name"] == "Ready"
    assert rows[0]["audience_type"] == "Longevity"
    assert rows[0]["lead_type"] == "Sponsor Page"
    assert rows[0]["sponsorship_probability"] == "65"


def test_review_queue_sorts_by_sponsorship_probability(tmp_path) -> None:
    leads = [
        Lead(
            entity_name="Lower Probability",
            url="https://lower.example",
            fit_score=95,
            sponsorship_probability=60,
            audience_type="Longevity",
            lead_type="Newsletter",
            compliance_risk="low",
            sponsor_signal="advertise_or_sponsor",
            source_urls=["https://lower.example"],
        ),
        Lead(
            entity_name="Higher Probability",
            url="https://higher.example",
            fit_score=70,
            sponsorship_probability=90,
            audience_type="Longevity",
            lead_type="Media Kit",
            compliance_risk="low",
            sponsor_signal="media_kit",
            source_urls=["https://higher.example"],
        ),
        Lead(
            entity_name="Directory",
            url="https://directory.example",
            audience_description="A curated roundup directory of top longevity newsletters.",
            fit_score=85,
            sponsorship_probability=80,
            audience_type="Longevity",
            lead_type="Newsletter",
            compliance_risk="low",
            sponsor_signal="advertise_or_sponsor",
            source_urls=["https://directory.example"],
        ),
    ]

    CSVExporter(tmp_path).export_all(leads)

    with (tmp_path / "leads_review_queue.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [row["entity_name"] for row in rows] == ["Higher Probability", "Lower Probability"]
