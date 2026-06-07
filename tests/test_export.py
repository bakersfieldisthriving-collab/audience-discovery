import csv

from audience_discovery.export.csv_exporter import CSVExporter
from audience_discovery.models import Lead


def test_csv_export_outputs_review_queue(tmp_path) -> None:
    leads = [
        Lead(
            entity_name="Ready",
            url="https://ready.example",
            fit_score=75,
            compliance_risk="low",
            sponsor_signal="advertise_or_sponsor",
            source_urls=["https://ready.example"],
        ),
        Lead(
            entity_name="Risky",
            url="https://risky.example",
            fit_score=90,
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
