from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin

import requests

from .models import Advert
from .parser import parse_adverts

DEFAULT_BASE_URL = "https://honda.appmoto.net"
DEFAULT_QUERY = "CL500"


@dataclass(frozen=True)
class ScraperConfig:
    base_url: str = DEFAULT_BASE_URL
    query: str = DEFAULT_QUERY
    timeout_seconds: int = 30
    user_agent: str = "CL500Monitor/0.1 (+personal low-frequency monitor)"

    @property
    def search_urls(self) -> list[str]:
        encoded = quote_plus(self.query)
        base = self.base_url.rstrip("/")
        return [
            f"{base}/?s={encoded}",
            f"{base}/search?query={encoded}",
            f"{base}/motos?search={encoded}",
        ]


class CL500Scraper:
    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

    def fetch_url(self, url: str) -> str:
        response = self.session.get(url, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        return response.text

    def scrape(self) -> list[Advert]:
        adverts: list[Advert] = []
        seen: set[str] = set()
        errors: list[str] = []

        for url in self.config.search_urls:
            try:
                html = self.fetch_url(url)
            except requests.RequestException as exc:
                errors.append(f"{url}: {exc}")
                continue
            for advert in parse_adverts(html, base_url=urljoin(url, "/")):
                if advert.source_id not in seen:
                    seen.add(advert.source_id)
                    adverts.append(advert)

        if not adverts and errors:
            raise RuntimeError("No se pudo recuperar ningún anuncio. Errores: " + "; ".join(errors))
        return adverts
