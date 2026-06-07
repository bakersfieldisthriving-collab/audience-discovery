from __future__ import annotations

import sqlite3
from pathlib import Path

from audience_discovery.models import LEAD_FIELDS, Lead, normalize_domain, utc_now_iso


class LeadStore:
    def __init__(self, db_path: str | Path = "outputs/leads.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def close(self) -> None:
        self.connection.close()

    def create_tables(self) -> None:
        columns = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_name TEXT NOT NULL,
            category TEXT NOT NULL,
            platform TEXT NOT NULL,
            url TEXT NOT NULL,
            domain TEXT NOT NULL,
            audience_description TEXT NOT NULL,
            audience_size_estimate TEXT NOT NULL,
            sponsor_signal TEXT NOT NULL,
            contact_method TEXT NOT NULL,
            public_contact TEXT NOT NULL,
            fit_score INTEGER NOT NULL,
            compliance_risk TEXT NOT NULL,
            fit_reason TEXT NOT NULL,
            outreach_angle TEXT NOT NULL,
            source_urls TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(domain, entity_name)
        """
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS leads ({columns})")
        self.connection.commit()

    def upsert_lead(self, lead: Lead) -> Lead:
        lead.domain = normalize_domain(lead.domain)
        incoming = lead.to_dict()
        existing = self._find_existing(lead)
        if existing:
            merged_sources = sorted(set(existing.source_urls + lead.source_urls))
            lead.created_at = existing.created_at
            lead.updated_at = utc_now_iso()
            lead.source_urls = merged_sources
            lead.status = existing.status if existing.status != "new" else lead.status
            data = lead.to_dict()
            assignments = ", ".join(f"{field}=?" for field in LEAD_FIELDS if field != "created_at")
            values = [data[field] for field in LEAD_FIELDS if field != "created_at"]
            values.extend([existing.domain, existing.entity_name])
            self.connection.execute(
                f"UPDATE leads SET {assignments} WHERE domain=? AND entity_name=?",
                values,
            )
        else:
            placeholders = ", ".join("?" for _ in LEAD_FIELDS)
            self.connection.execute(
                f"INSERT INTO leads ({', '.join(LEAD_FIELDS)}) VALUES ({placeholders})",
                [incoming[field] for field in LEAD_FIELDS],
            )
        self.connection.commit()
        return lead

    def _find_existing(self, lead: Lead) -> Lead | None:
        row = self.connection.execute(
            "SELECT * FROM leads WHERE domain=? AND entity_name=?",
            (lead.domain, lead.entity_name),
        ).fetchone()
        if row:
            return Lead.from_row(dict(row))
        if lead.domain != "unknown":
            row = self.connection.execute(
                "SELECT * FROM leads WHERE domain=? ORDER BY id LIMIT 1",
                (lead.domain,),
            ).fetchone()
            if row:
                return Lead.from_row(dict(row))
        return None

    def list_leads(self) -> list[Lead]:
        rows = self.connection.execute("SELECT * FROM leads ORDER BY fit_score DESC, updated_at DESC").fetchall()
        return [Lead.from_row(dict(row)) for row in rows]
