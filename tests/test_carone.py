import httpx
import respx

from app.carone import BASE_URL, LISTING_PATH, CaroneClient

SAMPLE_LISTING_HTML = """
<ol class="products list items product-items">
  <li class="item product product-item carone-product-item carone-product-item-5251">
    <div class="product-item-info carone-product-item-info" data-container="product-grid">
      <div class="product_image">
        <a data-product-id="5251" href="https://carone.com.uy/changan-uni-t-15t-5p-at-sku83-0004" class="product photo product-item-photo">
          <img src="https://cdn.impel.io/example/5251/thumb-lg.jpg">
        </a>
      </div>
      <div class="product details product-item-details carone-product-item-details">
        <div class="carone-car-info">
          <a href="https://carone.com.uy/changan-uni-t-15t-5p-at-sku83-0004" class="link-primary">
            <div class="carone-car-info-data">
              <p class="carone-car-info-data-brand cursor-pointer">Changan UNI-T</p>
              <p class="carone-car-info-data-model" title="UNI-T 1.5T 5P AT">UNI-T 1.5T 5P AT</p>
            </div>
          </a>
        </div>
        <a href="https://carone.com.uy/changan-uni-t-15t-5p-at-sku83-0004" class="link-primary">
          <div class="price-box price-final_price">
            <span class="normal-price">
              <span class="price-container price-final_price tax weee">
                <span class="price-label">Desde</span>
                <span id="product-price-5251" data-price-amount="34990" data-price-type="finalPrice" class="price-wrapper ">
                  <span class="price">US$&nbsp;34.990</span>
                </span>
              </span>
            </span>
          </div>
          <div class="carone-car-attributes">
            <div class="carone-car-attribute"><p class="carone-car-attribute-value">2025</p><p class="carone-car-attribute-title nomargin">Año</p></div>
            <div class="carone-car-attribute"><p class="carone-car-attribute-value">0</p><p class="carone-car-attribute-title nomargin">Kilómetros</p></div>
            <div class="carone-car-attribute"><p class="carone-car-attribute-value">NAFTA</p><p class="carone-car-attribute-title nomargin">Combustible</p></div>
          </div>
        </a>
      </div>
    </div>
  </li>
</ol>
"""

EMPTY_LISTING_HTML = '<ol class="products list items product-items"></ol>'


def test_parse_listings_extracts_normalized_fields():
    listings = CaroneClient._parse_listings(SAMPLE_LISTING_HTML)

    assert len(listings) == 1
    listing = listings[0]
    assert listing.id == "carone-5251"
    assert listing.source == "carone"
    assert listing.title == "Changan UNI-T UNI-T 1.5T 5P AT"
    assert listing.brand == "Changan UNI-T"
    assert listing.model == "UNI-T 1.5T 5P AT"
    assert listing.price == 34990.0
    assert listing.currency == "USD"
    assert listing.year == 2025
    assert listing.mileage_km == 0
    assert listing.url == "https://carone.com.uy/changan-uni-t-15t-5p-at-sku83-0004"
    assert listing.thumbnail == "https://cdn.impel.io/example/5251/thumb-lg.jpg"


def test_parse_listings_skips_items_without_a_link():
    listings = CaroneClient._parse_listings("<li class='item product product-item'></li>")

    assert listings == []


async def test_search_cars_stops_paginating_once_a_page_is_empty():
    async with httpx.AsyncClient(base_url=BASE_URL) as http_client:
        client = CaroneClient(http_client)
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(LISTING_PATH, params={"p": "2"}).respond(text=EMPTY_LISTING_HTML)
            page_one = mock.get(LISTING_PATH).respond(text=SAMPLE_LISTING_HTML)

            listings = await client.search_cars()

    assert page_one.called
    assert len(listings) == 1


async def test_search_cars_filters_results_by_query():
    async with httpx.AsyncClient(base_url=BASE_URL) as http_client:
        client = CaroneClient(http_client)
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(LISTING_PATH, params={"p": "2"}).respond(text=EMPTY_LISTING_HTML)
            mock.get(LISTING_PATH).respond(text=SAMPLE_LISTING_HTML)

            matching = await client.search_cars(query="changan")
            empty = await client.search_cars(query="toyota")

    assert len(matching) == 1
    assert empty == []
