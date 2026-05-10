from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256


@dataclass(frozen=True)
class Advert:
    """Structured representation of one motorcycle advert."""

    source_id: str
    url: str
    title: str
    price_eur: int | None = None
    mileage_km: int | None = None
    model_year: int | None = None
    location: str | None = None
    dealer: str | None = None
    extras: str | None = None
    raw_text: str | None = None
    fetched_at: datetime | None = None

    def normalized_fetched_at(self) -> datetime:
        return self.fetched_at or datetime.now(timezone.utc)

    @property
    def content_hash(self) -> str:
        payload = "|".join(
            [
                self.source_id,
                self.url,
                self.title,
                str(self.price_eur or ""),
                str(self.mileage_km or ""),
                str(self.model_year or ""),
                self.location or "",
                self.dealer or "",
                self.extras or "",
                self.raw_text or "",
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Change:
    """Detected change between two observations for one advert."""

    source_id: str
    field: str
    old_value: str | None
    new_value: str | None
    detected_at: datetime
