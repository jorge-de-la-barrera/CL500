from __future__ import annotations

import re
from hashlib import sha256
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import Advert

PRICE_RE = re.compile(r"(?P<value>\d{1,3}(?:[.\s]\d{3})*|\d+)\s*€")
KM_RE = re.compile(r"(?P<value>\d{1,3}(?:[.\s]\d{3})*|\d+)\s*km", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")


def parse_int(value: str) -> int | None:
    digits = re.sub(r"\D", "", value)
    return int(digits) if digits else None


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_price(text: str) -> int | None:
    match = PRICE_RE.search(text)
    return parse_int(match.group("value")) if match else None


def parse_mileage(text: str) -> int | None:
    match = KM_RE.search(text)
    return parse_int(match.group("value")) if match else None


def parse_year(text: str) -> int | None:
    matches = [int(m.group(0)) for m in YEAR_RE.finditer(text)]
    candidates = [year for year in matches if 2010 <= year <= 2035]
    return candidates[0] if candidates else None


def make_source_id(url: str, title: str) -> str:
    return sha256(f"{url}|{title}".encode("utf-8")).hexdigest()[:16]


def looks_like_cl500(text: str) -> bool:
    normalized = text.lower().replace("-", " ")
    return "cl500" in normalized or "cl 500" in normalized


def extract_candidate_nodes(soup: BeautifulSoup) -> list[object]:
    candidates: list[object] = []
    for node in soup.find_all(["article", "li", "div"]):
        text = compact_text(node.get_text(" ", strip=True))
        if len(text) < 20:
            continue
        if looks_like_cl500(text) and ("€" in text or "km" in text.lower()):
            candidates.append(node)
    return candidates


def parse_adverts(html: str, base_url: str) -> list[Advert]:
    soup = BeautifulSoup(html, "html.parser")
    adverts: list[Advert] = []
    seen: set[str] = set()

    for node in extract_candidate_nodes(soup):
        text = compact_text(node.get_text(" ", strip=True))
        link = node.find("a", href=True) if hasattr(node, "find") else None
        url = urljoin(base_url, link["href"]) if link else base_url
        title = extract_title(node, text)
        source_id = make_source_id(url, title)
        if source_id in seen:
            continue
        seen.add(source_id)
        adverts.append(
            Advert(
                source_id=source_id,
                url=url,
                title=title,
                price_eur=parse_price(text),
                mileage_km=parse_mileage(text),
                model_year=parse_year(text),
                location=extract_by_label(text, ("ubicación", "localidad", "provincia")),
                dealer=extract_by_label(text, ("concesionario", "vendedor")),
                extras=extract_extras(text),
                raw_text=text,
            )
        )
    return adverts


def extract_title(node: object, fallback_text: str) -> str:
    if hasattr(node, "find"):
        heading = node.find(["h1", "h2", "h3", "h4"])
        if heading:
            heading_text = compact_text(heading.get_text(" ", strip=True))
            if heading_text:
                return heading_text
    parts = re.split(r"\s{2,}|\s+-\s+|\s+\|\s+", fallback_text)
    return compact_text(parts[0])[:120]


def extract_by_label(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        pattern = re.compile(rf"{label}\s*:?\s*([^|,;]+)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            value = compact_text(match.group(1))
            return value[:120] if value else None
    return None


def extract_extras(text: str) -> str | None:
    keywords = ["travel", "pack", "extras", "accesorios", "maletas", "cúpula", "defensas"]
    lowered = text.lower()
    if not any(keyword in lowered for keyword in keywords):
        return None
    snippets: list[str] = []
    sentences = re.split(r"(?<=[.;])\s+|\s+\|\s+", text)
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in keywords):
            snippets.append(compact_text(sentence))
    return " | ".join(snippets)[:500] if snippets else None
