from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.aggregator import CarAggregator
from app.carone import CaroneClient
from app.mercadolibre import MercadoLibreClient
from app.models import CarListing

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.aggregator = CarAggregator([CaroneClient(), MercadoLibreClient()])
    yield
    await app.state.aggregator.aclose()


app = FastAPI(title="Uruguay Car Aggregator", lifespan=lifespan)


@app.get("/api/cars")
async def search_cars(request: Request, q: str | None = Query(default=None), limit: int = Query(default=30, le=50)) -> dict:
    listings: list[CarListing] = await request.app.state.aggregator.search_cars(query=q, limit=limit)
    return {"count": len(listings), "results": listings}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, q: str | None = Query(default=None)):
    listings = await request.app.state.aggregator.search_cars(query=q, limit=30)
    return templates.TemplateResponse(request, "index.html", {"listings": listings, "query": q or ""})
