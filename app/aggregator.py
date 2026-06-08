import asyncio
import logging
from typing import Protocol

from app.models import CarListing

logger = logging.getLogger(__name__)


class CarSource(Protocol):
    async def search_cars(self, query: str | None = None, limit: int = 30) -> list[CarListing]: ...

    async def aclose(self) -> None: ...


class CarAggregator:
    """Queries multiple car listing sources concurrently and merges whatever succeeds.

    A source failing (e.g. a marketplace blocking unauthenticated API access, or a
    scraped site changing its markup) shouldn't take down the whole page — its
    results are just skipped and logged.
    """

    def __init__(self, sources: list[CarSource]):
        self._sources = sources

    async def aclose(self) -> None:
        await asyncio.gather(*(source.aclose() for source in self._sources))

    async def search_cars(self, query: str | None = None, limit: int = 30) -> list[CarListing]:
        results = await asyncio.gather(
            *(source.search_cars(query=query, limit=limit) for source in self._sources),
            return_exceptions=True,
        )

        listings: list[CarListing] = []
        for source, result in zip(self._sources, results):
            if isinstance(result, BaseException):
                logger.warning("Source %s failed: %s", type(source).__name__, result)
                continue
            listings.extend(result)
        return listings
