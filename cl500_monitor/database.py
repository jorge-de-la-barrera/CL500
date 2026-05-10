from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = '''
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_url TEXT UNIQUE,
    title TEXT,
    price_eur INTEGER,
    km INTEGER,
    location TEXT,
    description TEXT,
    raw_text TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''


def get_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def upsert_ad(conn: sqlite3.Connection, ad: dict[str, Any]) -> None:
    conn.execute(
        '''
        INSERT INTO ads (
            ad_url,
            title,
            price_eur,
            km,
            location,
            description,
            raw_text,
            last_seen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(ad_url)
        DO UPDATE SET
            title=excluded.title,
            price_eur=excluded.price_eur,
            km=excluded.km,
            location=excluded.location,
            description=excluded.description,
            raw_text=excluded.raw_text,
            last_seen=CURRENT_TIMESTAMP
        ''',
        (
            ad.get('ad_url'),
            ad.get('title'),
            ad.get('price_eur'),
            ad.get('km'),
            ad.get('location'),
            ad.get('description'),
            ad.get('raw_text'),
        )
    )
    conn.commit()
