from app.aggregator import CarAggregator
from app.models import CarListing


class _StubSource:
    def __init__(self, listings: list[CarListing] | None = None, error: Exception | None = None):
        self._listings = listings or []
        self._error = error

    async def search_cars(self, query=None, limit=30):
        if self._error is not None:
            raise self._error
        return self._listings

    async def aclose(self):
        pass


def _listing(listing_id: str, source: str) -> CarListing:
    return CarListing(id=listing_id, source=source, title="Some car", price=1.0, currency="USD", url="https://example.com")


async def test_search_cars_merges_results_from_all_sources():
    aggregator = CarAggregator(
        [
            _StubSource([_listing("1", "carone")]),
            _StubSource([_listing("2", "mercadolibre"), _listing("3", "mercadolibre")]),
        ]
    )

    listings = await aggregator.search_cars(query="corolla")

    assert {listing.id for listing in listings} == {"1", "2", "3"}


async def test_search_cars_skips_failing_sources():
    aggregator = CarAggregator(
        [
            _StubSource([_listing("1", "carone")]),
            _StubSource(error=RuntimeError("source is down")),
        ]
    )

    listings = await aggregator.search_cars()

    assert [listing.id for listing in listings] == ["1"]
