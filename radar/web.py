"""Local buyer workspace. No production authentication or payment operations."""
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from radar.community import router
from radar.core import calculate_margin
from radar.offers import connect

app = FastAPI(title="Radar Buyer Workspace", version="0.5.0")
app.include_router(router)
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


@app.get("/admin", include_in_schema=False)
@app.get("/travel", include_in_schema=False)
def workspace_sections():
    return FileResponse(ROOT / "web" / "community.html")
