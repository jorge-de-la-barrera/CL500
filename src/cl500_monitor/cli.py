from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

from .db import AdvertStore
from .scraper import CL500Scraper, ScraperConfig

DEFAULT_DB = Path(os.environ.get("CL500_DB", "data/cl500.sqlite"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor de anuncios Honda CL500")
    subparsers = parser.add_subparsers(dest="command")

    scrape = subparsers.add_parser("scrape", help="Recupera anuncios y actualiza SQLite")
    scrape.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base SQLite")
    scrape.add_argument("--base-url", default=os.environ.get("CL500_BASE_URL", "https://honda.appmoto.net"))
    scrape.add_argument("--query", default=os.environ.get("CL500_QUERY", "CL500"))

    list_cmd = subparsers.add_parser("list", help="Lista anuncios activos")
    list_cmd.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base SQLite")
    list_cmd.add_argument("--all", action="store_true", help="Incluye anuncios inactivos")

    changes = subparsers.add_parser("changes", help="Lista cambios detectados")
    changes.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base SQLite")
    changes.add_argument("--limit", type=int, default=50)

    parser.set_defaults(command="scrape")
    return parser


def cmd_scrape(args: argparse.Namespace) -> int:
    scraper = CL500Scraper(ScraperConfig(base_url=args.base_url, query=args.query))
    adverts = scraper.scrape()
    store = AdvertStore(args.db)
    changes = store.upsert_many(adverts)
    print(f"Anuncios recuperados: {len(adverts)}")
    print(f"Cambios detectados: {len(changes)}")
    for change in changes:
        print(f"- {change.source_id} {change.field}: {change.old_value!r} -> {change.new_value!r}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = AdvertStore(args.db)
    rows = store.list_adverts(active_only=not args.all)
    if not rows:
        print("No hay anuncios registrados.")
        return 0
    for row in rows:
        price = f"{row['price_eur']} €" if row["price_eur"] is not None else "precio desconocido"
        km = f"{row['mileage_km']} km" if row["mileage_km"] is not None else "km desconocidos"
        active = "activo" if row["is_active"] else "inactivo"
        print(f"[{active}] {row['title']} | {price} | {km} | {row['url']}")
    return 0


def cmd_changes(args: argparse.Namespace) -> int:
    store = AdvertStore(args.db)
    rows = store.list_changes(limit=args.limit)
    if not rows:
        print("No hay cambios registrados.")
        return 0
    for row in rows:
        print(
            f"{row['detected_at']} {row['source_id']} {row['field']}: "
            f"{row['old_value']!r} -> {row['new_value']!r}"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scrape":
        return cmd_scrape(args)
    if args.command == "list":
        return cmd_list(args)
    if args.command == "changes":
        return cmd_changes(args)
    parser.error(f"Comando desconocido: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
