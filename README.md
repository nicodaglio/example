# Uruguay Car Aggregator (MVP)

Aggregates car listings in Uruguay. The MVP pulls from the **MercadoLibre
Uruguay public API** (no API key needed for search) and shows them on a
single page with a basic search box, plus a JSON endpoint.

Other sources discussed for later phases:

- **Houses**: MercadoLibre, InfoCasas, VeoCasas (likely scraping — check each
  site's terms of service first).
- **Facebook Marketplace**: intentionally left out. It has no public API and
  scraping it violates Meta's terms of service, so it's not a viable source
  for now.

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

Tests mock the MercadoLibre API with `respx`, so they run without network access.

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
