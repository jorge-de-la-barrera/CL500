from cl500_monitor.db import AdvertStore
from cl500_monitor.models import Advert


def test_store_detects_price_change(tmp_path) -> None:
    db_path = tmp_path / "cl500.sqlite"
    store = AdvertStore(db_path)

    first = Advert(source_id="a1", url="https://example.test/a1", title="Honda CL500", price_eur=6900)
    second = Advert(source_id="a1", url="https://example.test/a1", title="Honda CL500", price_eur=6700)

    assert store.upsert_many([first]) == []
    changes = store.upsert_many([second])

    assert len(changes) == 1
    assert changes[0].field == "price_eur"
    assert changes[0].old_value == "6900"
    assert changes[0].new_value == "6700"
