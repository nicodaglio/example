from pydantic import BaseModel


class CarListing(BaseModel):
    """Normalized car listing, independent of which marketplace it came from."""

    id: str
    source: str
    title: str
    price: float
    currency: str
    url: str
    thumbnail: str | None = None
    location: str | None = None
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    mileage_km: int | None = None
