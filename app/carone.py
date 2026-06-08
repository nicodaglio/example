import re

import httpx
from bs4 import BeautifulSoup, Tag

from app.models import CarListing

BASE_URL = "https://carone.com.uy"
LISTING_PATH = "/autos-usados-y-0km"

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Maps CarOne's (Spanish, accented) attribute labels to our normalized field names.
_ATTRIBUTE_FIELD_MAP = {
    "año": "year",
    "kilómetros": "mileage_km",
}

_NON_DIGITS_RE = re.compile(r"[^\d]")


class CaroneClient:
    """Scrapes new/used car listings from the CarOne dealership site (carone.com.uy).

    CarOne has no public API, so this parses its server-rendered listing pages.
    There's no free-text search on that listing page, so `query` is applied as a
    client-side filter over the scraped titles.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self._client = http_client or httpx.AsyncClient(
            base_url=BASE_URL, timeout=10.0, headers=_DEFAULT_HEADERS, follow_redirects=True
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_cars(self, query: str | None = None, limit: int = 30, max_pages: int = 3) -> list[CarListing]:
        listings: list[CarListing] = []
        for page in range(1, max_pages + 1):
            params = {"p": page} if page > 1 else {}
            response = await self._client.get(LISTING_PATH, params=params)
            response.raise_for_status()

            page_listings = self._parse_listings(response.text)
            if not page_listings:
                break
            listings.extend(page_listings)
            if len(listings) >= limit:
                break

        if query:
            needle = query.strip().lower()
            listings = [listing for listing in listings if needle in (listing.title or "").lower()]

        return listings[:limit]

    @classmethod
    def _parse_listings(cls, html: str) -> list[CarListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings = []
        for item in soup.select("li.product-item"):
            listing = cls._parse_item(item)
            if listing is not None:
                listings.append(listing)
        return listings

    @classmethod
    def _parse_item(cls, item: Tag) -> CarListing | None:
        link = item.select_one("a.product-item-photo")
        if link is None or not link.get("href"):
            return None

        url = link["href"]
        product_id = link.get("data-product-id") or url.rstrip("/").rsplit("-", 1)[-1]
        image = link.select_one("img")
        thumbnail = image.get("src") if image else None

        brand = cls._text(item.select_one(".carone-car-info-data-brand"))
        model = cls._title_or_text(item.select_one(".carone-car-info-data-model"))
        title = " ".join(part for part in (brand, model) if part) or brand or model or "Auto"

        price_el = item.select_one("[data-price-amount]")
        price = float(price_el["data-price-amount"]) if price_el and price_el.get("data-price-amount") else 0.0
        currency = cls._parse_currency(cls._text(price_el))

        fields: dict[str, int] = {}
        for attribute in item.select(".carone-car-attribute"):
            label = cls._text(attribute.select_one(".carone-car-attribute-title"))
            value = cls._text(attribute.select_one(".carone-car-attribute-value"))
            field_name = _ATTRIBUTE_FIELD_MAP.get((label or "").lower())
            if field_name and value:
                parsed = cls._parse_int(value)
                if parsed is not None:
                    fields[field_name] = parsed

        return CarListing(
            id=f"carone-{product_id}",
            source="carone",
            title=title,
            price=price,
            currency=currency,
            url=url,
            thumbnail=thumbnail,
            brand=brand,
            model=model,
            **fields,
        )

    @staticmethod
    def _text(node: Tag | None) -> str | None:
        return node.get_text(strip=True) if node else None

    @classmethod
    def _title_or_text(cls, node: Tag | None) -> str | None:
        if node is None:
            return None
        return node.get("title") or cls._text(node)

    @staticmethod
    def _parse_currency(text: str | None) -> str:
        return "USD" if (text or "").strip().upper().startswith("US$") else "UYU"

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = _NON_DIGITS_RE.sub("", value)
        return int(digits) if digits else None
