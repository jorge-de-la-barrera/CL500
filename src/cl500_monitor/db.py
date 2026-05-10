from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from .models import Advert, Change

SCHEMA = """
CREATE TABLE IF NOT EXISTS adverts (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    price_eur INTEGER,
    mileage_km INTEGER,
    model_year INTEGER,
    location TEXT,
    dealer TEXT,
    extras TEXT,
    raw_text TEXT,
    content_hash TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS advert_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    price_eur INTEGER,
    mileage_km INTEGER,
    model_year INTEGER,
    location TEXT,
    dealer TEXT,
    extras TEXT,
    raw_text TEXT,
    content_hash TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_source_id ON advert_snapshots(source_id);
CREATE INDEX IF NOT EXISTS idx_changes_source_id ON changes(source_id);
"""

TRACKED_FIELDS = ("title", "price_eur", "mileage_km", "model_year", "location", "dealer", "extras")


class AdvertStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_many(self, adverts: Iterable[Advert]) -> list[Change]:
        self.init()
        detected: list[Change] = []
        seen_ids: set[str] = set()
        with self.connect() as conn:
            for advert in adverts:
                seen_ids.add(advert.source_id)
                detected.extend(self._upsert_one(conn, advert))
            self._mark_missing_as_inactive(conn, seen_ids)
        return detected

    def _upsert_one(self, conn: sqlite3.Connection, advert: Advert) -> list[Change]:
        fetched_at = advert.normalized_fetched_at().astimezone(timezone.utc).isoformat()
        old = conn.execute(
            "SELECT * FROM adverts WHERE source_id = ?", (advert.source_id,)
        ).fetchone()
        changes = self._detect_changes(old, advert, fetched_at) if old else []

        conn.execute(
            """
            INSERT INTO advert_snapshots (
                source_id, url, title, price_eur, mileage_km, model_year, location,
                dealer, extras, raw_text, content_hash, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                advert.source_id,
                advert.url,
                advert.title,
                advert.price_eur,
                advert.mileage_km,
                advert.model_year,
                advert.location,
                advert.dealer,
                advert.extras,
                advert.raw_text,
                advert.content_hash,
                fetched_at,
            ),
        )

        if old is None:
            conn.execute(
                """
                INSERT INTO adverts (
                    source_id, url, title, price_eur, mileage_km, model_year, location,
                    dealer, extras, raw_text, content_hash, first_seen_at, last_seen_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    advert.source_id,
                    advert.url,
                    advert.title,
                    advert.price_eur,
                    advert.mileage_km,
                    advert.model_year,
                    advert.location,
                    advert.dealer,
                    advert.extras,
                    advert.raw_text,
                    advert.content_hash,
                    fetched_at,
                    fetched_at,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE adverts SET
                    url = ?, title = ?, price_eur = ?, mileage_km = ?, model_year = ?,
                    location = ?, dealer = ?, extras = ?, raw_text = ?, content_hash = ?,
                    last_seen_at = ?, is_active = 1
                WHERE source_id = ?
                """,
                (
                    advert.url,
                    advert.title,
                    advert.price_eur,
                    advert.mileage_km,
                    advert.model_year,
                    advert.location,
                    advert.dealer,
                    advert.extras,
                    advert.raw_text,
                    advert.content_hash,
                    fetched_at,
                    advert.source_id,
                ),
            )

        for change in changes:
            conn.execute(
                """
                INSERT INTO changes (source_id, field, old_value, new_value, detected_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    change.source_id,
                    change.field,
                    change.old_value,
                    change.new_value,
                    change.detected_at.isoformat(),
                ),
            )
        return changes

    def _detect_changes(
        self, old: sqlite3.Row, advert: Advert, fetched_at: str
    ) -> list[Change]:
        detected_at = datetime.fromisoformat(fetched_at)
        changes: list[Change] = []
        for field in TRACKED_FIELDS:
            old_value = old[field]
            new_value = getattr(advert, field)
            if old_value != new_value:
                changes.append(
                    Change(
                        source_id=advert.source_id,
                        field=field,
                        old_value=None if old_value is None else str(old_value),
                        new_value=None if new_value is None else str(new_value),
                        detected_at=detected_at,
                    )
                )
        return changes

    def _mark_missing_as_inactive(self, conn: sqlite3.Connection, seen_ids: set[str]) -> None:
        if not seen_ids:
            return
        placeholders = ",".join("?" for _ in seen_ids)
        conn.execute(
            f"UPDATE adverts SET is_active = 0 WHERE source_id NOT IN ({placeholders})",
            tuple(seen_ids),
        )

    def list_adverts(self, active_only: bool = True) -> list[sqlite3.Row]:
        self.init()
        sql = "SELECT * FROM adverts"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY price_eur IS NULL, price_eur ASC, last_seen_at DESC"
        with self.connect() as conn:
            return list(conn.execute(sql))

    def list_changes(self, limit: int = 50) -> list[sqlite3.Row]:
        self.init()
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM changes ORDER BY detected_at DESC, id DESC LIMIT ?", (limit,)
                )
            )
