import re

import httpx

from app.models import CarListing

SITE_ID = "MLU"  # MercadoLibre Uruguay
BASE_URL = "https://api.mercadolibre.com"

# Maps MercadoLibre item attribute IDs to our normalized field names.
_ATTRIBUTE_FIELD_MAP = {
    "BRAND": "brand",
    "MODEL": "model",
    "VEHICLE_YEAR": "year",
    "KILOMETERS": "mileage_km",
}

_DIGITS_RE = re.compile(r"[\d.,]+")

# MercadoLibre's API rejects requests whose User-Agent identifies them as a
# script (e.g. httpx's default "python-httpx/x.y.z"), so we send a
# browser-like one instead.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class MercadoLibreClient:
    """Thin async client around the public MercadoLibre search API for Uruguay."""

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, timeout=10.0, headers=_DEFAULT_HEADERS)
        self._vehicles_category_id: str | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_cars(self, query: str | None = None, limit: int = 30, offset: int = 0) -> list[CarListing]:
        category_id = await self._resolve_vehicles_category_id()
        params: dict[str, str | int] = {"category": category_id, "limit": limit, "offset": offset}
        if query:
            params["q"] = query

        response = await self._client.get(f"/sites/{SITE_ID}/search", params=params)
        response.raise_for_status()

        return [self._normalize(item) for item in response.json().get("results", [])]

    async def _resolve_vehicles_category_id(self) -> str:
        """Looks up the "Vehículos" category ID for MLU instead of hardcoding it,
        since MercadoLibre category IDs are opaque and can differ per site."""
        if self._vehicles_category_id is not None:
            return self._vehicles_category_id

        response = await self._client.get(f"/sites/{SITE_ID}/categories")
        response.raise_for_status()

        for category in response.json():
            name = category["name"].lower()
            if "vehículo" in name or "vehiculo" in name:
                self._vehicles_category_id = category["id"]
                return self._vehicles_category_id

        raise RuntimeError(f"Could not find a vehicles category for site {SITE_ID}")

    @classmethod
    def _normalize(cls, item: dict) -> CarListing:
        attributes = {attr["id"]: attr.get("value_name") for attr in item.get("attributes", [])}
        fields: dict[str, object] = {}
        for attribute_id, field_name in _ATTRIBUTE_FIELD_MAP.items():
            value = attributes.get(attribute_id)
            if value is None:
                continue
            if field_name in ("year", "mileage_km"):
                value = cls._parse_int(value)
            if value is not None:
                fields[field_name] = value

        address = item.get("address") or {}
        location = ", ".join(filter(None, [address.get("city_name"), address.get("state_name")])) or None

        return CarListing(
            id=item["id"],
            source="mercadolibre",
            title=item["title"],
            price=item["price"],
            currency=item["currency_id"],
            url=item["permalink"],
            thumbnail=item.get("thumbnail"),
            location=location,
            **fields,
        )

    @staticmethod
    def _parse_int(value: str) -> int | None:
        match = _DIGITS_RE.search(value)
        if not match:
            return None
        digits = re.sub(r"[.,]", "", match.group())
        return int(digits) if digits else None
