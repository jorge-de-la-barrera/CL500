from __future__ import annotations

import argparse
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from cl500_monitor.database import get_connection, upsert_ad

BASE_URL = 'https://honda.appmoto.net/'
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) '
        'AppleWebKit/537.36 '
        '(KHTML, like Gecko) '
        'Chrome/124.0 Safari/537.36'
    )
}


def extract_int(text: str | None) -> int | None:
    if not text:
        return None

    digits = re.sub(r'[^0-9]', '', text)
    return int(digits) if digits else None


def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_ads(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, 'lxml')

    ads: list[dict[str, Any]] = []

    for article in soup.find_all(['article', 'div']):
        text = article.get_text(' ', strip=True)

        if 'CL500' not in text.upper():
            continue

        links = article.find_all('a', href=True)
        ad_url = None

        for link in links:
            href = link['href']
            if href.startswith('http'):
                ad_url = href
                break

        ads.append({
            'ad_url': ad_url or text[:100],
            'title': text[:120],
            'price_eur': extract_int(text),
            'km': None,
            'location': None,
            'description': text[:1000],
            'raw_text': text,
        })

    return ads


def run(db_path: str) -> None:
    html = fetch_page(BASE_URL)
    ads = parse_ads(html)

    conn = get_connection(db_path)

    for ad in ads:
        upsert_ad(conn, ad)
        print(f"stored: {ad['title']}")

    print(f'processed {len(ads)} ads')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--db',
        default='data/cl500.sqlite',
        help='SQLite database path'
    )
    return parser


if __name__ == '__main__':
    args = build_parser().parse_args()
    run(args.db)
