# Uruguay Car Aggregator (MVP)

Aggregates car listings in Uruguay from multiple sources and shows them on a
single page with a basic search box, plus a JSON endpoint.

## Sources

- **CarOne** (`app/carone.py`) — scrapes the dealership's server-rendered
  listing pages with `httpx` + `BeautifulSoup` (no public API available).
- **MercadoLibre Uruguay** (`app/mercadolibre.py`) — uses the public search
  API. **Currently returns 403 Forbidden even for unauthenticated, in-country
  requests** — MercadoLibre appears to now require OAuth for API access. The
  client is kept in place for when that's wired up (see "MercadoLibre auth"
  below); the aggregator skips it gracefully if it errors.

`app/aggregator.py` queries all sources concurrently and merges whatever
succeeds — one source failing (blocked API, changed markup, etc.) doesn't
take down the page.

Other sources discussed for later phases:

- **Houses**: MercadoLibre, InfoCasas, VeoCasas (likely scraping — check each
  site's terms of service first).
- **Facebook Marketplace**: intentionally left out. It has no public API and
  scraping it violates Meta's terms of service, so it's not a viable source
  for now.

## MercadoLibre auth (parked for now)

To use MercadoLibre's API you'd need to register a free app at
https://developers.mercadolibre.com.uy and implement OAuth2 (authorization
code flow: redirect → callback → exchange code for `access_token` +
`refresh_token`). Store `MELI_CLIENT_ID` / `MELI_CLIENT_SECRET` in a local
`.env` file (already gitignored) — never commit them.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000

- `GET /` — HTML page with a search box and listing cards.
- `GET /api/cars?q=corolla&limit=20` — JSON results.

## Tests

```bash
pytest
```

Tests mock external HTTP calls (`respx` for MercadoLibre, sample HTML fixtures
for CarOne), so they run without network access.

## Deploying for free (to test)

- **App + scheduled jobs**: [Render](https://render.com) or
  [Railway](https://railway.app) — connect this GitHub repo, free tier,
  Postgres included if/when persistence is added.
- **Periodic scraping/sync jobs**: GitHub Actions cron workflows (free,
  no server needs to run 24/7).
- **Frontend only** (if it's ever split out): [Vercel](https://vercel.com) or
  [Netlify](https://netlify.com).

## Notes

- The MercadoLibre vehicles category ID is resolved at runtime by name
  (`app/mercadolibre.py`) rather than hardcoded, since category IDs are
  opaque per-site identifiers.
