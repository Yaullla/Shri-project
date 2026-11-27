"""Local-only community CRM and trip board. No outreach, booking or payments."""
from contextlib import closing
from datetime import UTC, date, datetime
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from radar.access import admin, traveler
from radar.offers import connect

router = APIRouter(prefix="/api")


class Community(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    url: str = Field(max_length=300)
    country: str = Field(min_length=1, max_length=80)
    routes: str = Field(default="", max_length=300)
    audience: str = Field(default="", max_length=160)
    rules: str = Field(default="", max_length=2000)
    contact_status: Literal["new", "contacted", "permission_granted", "declined"] = "new"
    ad_cost_rub: int | None = Field(default=None, ge=0, le=10000000)
    leads: int = Field(default=0, ge=0, le=1000000)

    @field_validator("url")
    @classmethod
    def telegram_url(cls, value):
        url = urlsplit(value)
        if (url.scheme != "https" or url.netloc != "t.me" or not url.path.strip("/")
                or url.query or url.fragment or url.path.startswith("/+")
                or url.path.startswith("/joinchat/") or len(url.path.strip("/").split("/")) != 1):
            raise ValueError("Use a public https://t.me/channel URL")
        handle = url.path.strip("/")
        if not handle.isascii() or not handle.replace("_", "").isalnum():
            raise ValueError("Invalid public Telegram handle")
        return "https://t.me/" + handle.lower()


class Trip(BaseModel):
    origin: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    departure: date
    capacity_kg: float = Field(gt=0, le=50, allow_inf_nan=False)
    reward_rub: int = Field(ge=0, le=1000000)

    @field_validator("departure")
    @classmethod
    def future_date(cls, value):
        if value < datetime.now(UTC).date():
            raise ValueError("Departure is in the past")
        return value


def workspace_db():
    db = connect()
    db.execute("""CREATE TABLE IF NOT EXISTS communities (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT UNIQUE NOT NULL,
        country TEXT NOT NULL, routes TEXT NOT NULL, audience TEXT NOT NULL,
        rules TEXT NOT NULL, contact_status TEXT NOT NULL, ad_cost_rub INTEGER,
        leads INTEGER NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY, origin TEXT NOT NULL, destination TEXT NOT NULL,
        departure TEXT NOT NULL, capacity_kg REAL NOT NULL, reward_rub INTEGER NOT NULL)""")
    return db


@router.get("/communities", dependencies=[Depends(admin)])
def communities():
    with closing(workspace_db()) as db:
        return {"rows": [dict(r) for r in db.execute(
            "SELECT * FROM communities ORDER BY id DESC LIMIT 1000")]}


def save_community(body, entry_id=None):
    from sqlite3 import IntegrityError
    values = tuple(body.model_dump().values())
    try:
        with closing(workspace_db()) as db, db:
            if entry_id is None:
                result = db.execute("""INSERT INTO communities
                    (name,url,country,routes,audience,rules,contact_status,ad_cost_rub,leads)
                    VALUES (?,?,?,?,?,?,?,?,?)""", values)
                entry_id = result.lastrowid
            else:
                result = db.execute("""UPDATE communities SET name=?,url=?,country=?,routes=?,
                    audience=?,rules=?,contact_status=?,ad_cost_rub=?,leads=? WHERE id=?""",
                    (*values, entry_id))
                if result.rowcount != 1:
                    raise HTTPException(404, "Community not found")
            return dict(db.execute("SELECT * FROM communities WHERE id=?", (entry_id,)).fetchone())
    except IntegrityError as exc:
        raise HTTPException(409, "Telegram URL already exists") from exc


@router.post("/communities", status_code=201, dependencies=[Depends(admin)])
def create_community(body: Community):
    return save_community(body)


@router.put("/communities/{entry_id}", dependencies=[Depends(admin)])
def update_community(entry_id: int, body: Community):
    return save_community(body, entry_id)


@router.delete("/communities/{entry_id}", dependencies=[Depends(admin)])
def delete_community(entry_id: int):
    with closing(workspace_db()) as db, db:
        if db.execute("DELETE FROM communities WHERE id=?", (entry_id,)).rowcount != 1:
            raise HTTPException(404, "Community not found")
    return {"deleted": True}


@router.get("/trips", dependencies=[Depends(traveler)])
def trips():
    with closing(workspace_db()) as db:
        return {"rows": [dict(r) for r in db.execute(
            "SELECT * FROM trips ORDER BY departure,id LIMIT 1000")]}


@router.post("/trips", status_code=201, dependencies=[Depends(traveler)])
def create_trip(body: Trip):
    with closing(workspace_db()) as db, db:
        data = body.model_dump(mode="json")
        row = db.execute("""INSERT INTO trips
            (origin,destination,departure,capacity_kg,reward_rub) VALUES (?,?,?,?,?)""",
            tuple(data.values()))
        return {"id": row.lastrowid, **data}


@router.delete("/trips/{entry_id}", dependencies=[Depends(traveler)])
def delete_trip(entry_id: int):
    with closing(workspace_db()) as db, db:
        if db.execute("DELETE FROM trips WHERE id=?", (entry_id,)).rowcount != 1:
            raise HTTPException(404, "Trip not found")
    return {"deleted": True}
