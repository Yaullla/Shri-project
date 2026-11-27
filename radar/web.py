"""Local buyer workspace. No production authentication or payment operations."""
from contextlib import closing
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field

from radar.access import admin, traveler
from radar.community import router
from radar.core import calculate_margin
from radar.offers import connect

app = FastAPI(title="Radar Buyer Workspace", version="0.5.1")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
app.include_router(router)


@app.middleware("http")
async def private_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/admin", "/travel", "/api/communities", "/api/trips")):
        response.headers["Cache-Control"] = "no-store"
    return response


ROOT = Path(__file__).resolve().parents[1]


class Calculation(BaseModel):
    purchase_rub: float = Field(ge=0, le=1e9)
    sale_rub: float = Field(gt=0, le=1e9)
    shipping_rub: float = Field(default=0, ge=0, le=1e9)
    customs_rub: float = Field(default=0, ge=0, le=1e9)
    other_cost_rub: float = Field(default=0, ge=0, le=1e9)
    fee_percent: float = Field(default=0, ge=0, lt=100)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/observations")
def observations():
    with closing(connect()) as db:
        rows = db.execute("SELECT * FROM offers ORDER BY observed_at DESC LIMIT 100")
        return {"rows": [dict(row) for row in rows], "mode": "local_database"}


@app.post("/api/calculate")
def calculate(body: Calculation):
    return calculate_margin(**body.model_dump())


@app.get("/admin", include_in_schema=False, dependencies=[Depends(admin)])
@app.get("/travel", include_in_schema=False, dependencies=[Depends(traveler)])
def workspace_sections():
    return FileResponse(ROOT / "web" / "community.html")
