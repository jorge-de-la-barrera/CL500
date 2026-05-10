from cl500_monitor.parser import parse_adverts, parse_mileage, parse_price, parse_year


def test_parse_price() -> None:
    assert parse_price("Honda CL500 6.850 €") == 6850


def test_parse_mileage() -> None:
    assert parse_mileage("1.250 km") == 1250


def test_parse_year() -> None:
    assert parse_year("Matriculada en 2024") == 2024


def test_parse_adverts_extracts_basic_card() -> None:
    html = """
    <article>
      <a href="/motos/honda-cl500-123"><h2>Honda CL500 Travel</h2></a>
      <p>Precio 6.850 € · 1.250 km · año 2024 · Pack Travel con maletas</p>
    </article>
    """
    adverts = parse_adverts(html, "https://honda.appmoto.net")
    assert len(adverts) == 1
    advert = adverts[0]
    assert advert.title == "Honda CL500 Travel"
    assert advert.price_eur == 6850
    assert advert.mileage_km == 1250
    assert advert.model_year == 2024
    assert "Travel" in (advert.extras or "")
