from __future__ import annotations

import csv
from pathlib import Path

from audience_discovery.models import LEAD_FIELDS, Lead


def review_queue_filter(lead: Lead) -> bool:
    return lead.fit_score >= 60 and lead.compliance_risk != "high" and lead.sponsor_signal != "none"


class CSVExporter:
    def __init__(self, output_dir: str | Path = "outputs") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, leads: list[Lead]) -> dict[str, int]:
        raw_count = self._write("leads_raw.csv", leads)
        scored = sorted(leads, key=lambda lead: lead.fit_score, reverse=True)
        scored_count = self._write("leads_scored.csv", scored)
        review = [lead for lead in scored if review_queue_filter(lead)]
        review_count = self._write("leads_review_queue.csv", review)
        return {"raw": raw_count, "scored": scored_count, "review_queue": review_count}

    def _write(self, filename: str, leads: list[Lead]) -> int:
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=LEAD_FIELDS)
            writer.writeheader()
            for lead in leads:
                if not lead.source_urls:
                    continue
                writer.writerow(lead.to_dict())
        return len([lead for lead in leads if lead.source_urls])
