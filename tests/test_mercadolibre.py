import httpx
import respx

from app.mercadolibre import BASE_URL, SITE_ID, MercadoLibreClient

SAMPLE_ITEM = {
    "id": "MLU123",
    "title": "Toyota Corolla 2018",
    "price": 18000,
    "currency_id": "USD",
    "permalink": "https://articulo.mercadolibre.com.uy/MLU-123",
    "thumbnail": "https://example.com/thumb.jpg",
    "address": {"city_name": "Montevideo", "state_name": "Montevideo"},
    "attributes": [
        {"id": "BRAND", "value_name": "Toyota"},
        {"id": "MODEL", "value_name": "Corolla"},
        {"id": "VEHICLE_YEAR", "value_name": "2018"},
        {"id": "KILOMETERS", "value_name": "45.000 km"},
    ],
}


def test_normalize_extracts_known_attributes():
    listing = MercadoLibreClient._normalize(SAMPLE_ITEM)

    assert listing.source == "mercadolibre"
    assert listing.brand == "Toyota"
    assert listing.model == "Corolla"
    assert listing.year == 2018
    assert listing.mileage_km == 45000
    assert listing.location == "Montevideo, Montevideo"
    assert listing.url == SAMPLE_ITEM["permalink"]


def test_normalize_handles_missing_attributes():
    item = {**SAMPLE_ITEM, "attributes": []}

    listing = MercadoLibreClient._normalize(item)

    assert listing.brand is None
    assert listing.year is None
    assert listing.mileage_km is None


async def test_search_cars_resolves_category_then_normalizes_results():
    async with httpx.AsyncClient(base_url=BASE_URL) as http_client:
        client = MercadoLibreClient(http_client)
        with respx.mock(base_url=BASE_URL, assert_all_called=True) as mock:
            mock.get(f"/sites/{SITE_ID}/categories").respond(
                json=[
                    {"id": "MLU1430", "name": "Inmuebles"},
                    {"id": "MLU1744", "name": "Vehículos"},
                ]
            )
            search_route = mock.get(f"/sites/{SITE_ID}/search").respond(json={"results": [SAMPLE_ITEM]})

            listings = await client.search_cars(query="corolla")

    assert search_route.calls.last.request.url.params["category"] == "MLU1744"
    assert search_route.calls.last.request.url.params["q"] == "corolla"
    assert len(listings) == 1
    assert listings[0].title == "Toyota Corolla 2018"


async def test_search_cars_raises_when_vehicles_category_is_missing():
    async with httpx.AsyncClient(base_url=BASE_URL) as http_client:
        client = MercadoLibreClient(http_client)
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(f"/sites/{SITE_ID}/categories").respond(
                json=[{"id": "MLU1430", "name": "Inmuebles"}]
            )

            try:
                await client.search_cars()
            except RuntimeError as error:
                assert "vehicles category" in str(error)
            else:
                raise AssertionError("expected RuntimeError")
