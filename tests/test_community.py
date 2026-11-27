from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from radar.web import app
from radar.seed_communities import seed


def test_crm_crud(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "crm.sqlite3"))
    monkeypatch.setenv("RADAR_ADMIN_PASSWORD", "test-admin-long-password")
    client = TestClient(app)
    client.auth = ("admin", "test-admin-long-password")
    body = {"name": "Fixture", "url": "https://t.me/example_fixture",
            "country": "India", "routes": "IN-RU", "leads": 2}
    assert client.get("/api/communities").json() == {"rows": []}
    response = client.post("/api/communities", json=body)
    assert response.status_code == 201
    entry = response.json()["id"]
    assert client.post("/api/communities", json=body).status_code == 409
    assert client.put(f"/api/communities/{entry}", json=body | {"leads": 3}).json()["leads"] == 3
    assert client.get("/api/communities").json()["rows"][0]["leads"] == 3
    assert client.post("/api/communities", json=body | {"url": "https://t.me/+private"}).status_code == 422
    assert client.delete(f"/api/communities/{entry}").status_code == 200
    assert client.get("/api/communities").json() == {"rows": []}


def test_trip_board(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "trips.sqlite3"))
    monkeypatch.setenv("RADAR_TRAVELER_PASSWORD", "test-traveler-long-password")
    client = TestClient(app)
    client.auth = ("traveler", "test-traveler-long-password")
    body = {"origin": "Delhi", "destination": "Moscow",
            "departure": (datetime.now(UTC).date() + timedelta(days=1)).isoformat(),
            "capacity_kg": 2, "reward_rub": 1000}
    result = client.post("/api/trips", json=body)
    assert result.status_code == 201
    assert len(client.get("/api/trips").json()["rows"]) == 1
    assert client.post("/api/trips", json=body | {"capacity_kg": 51}).status_code == 422
    assert client.delete(f"/api/trips/{result.json()['id']}").status_code == 200
    assert client.get("/travel").status_code == 200
    assert client.get("/admin").status_code == 503


def test_access_gates(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "auth.sqlite3"))
    monkeypatch.delenv("RADAR_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("RADAR_TRAVELER_PASSWORD", raising=False)
    client = TestClient(app)
    assert client.get("/api/communities").status_code == 503
    assert client.get("/api/trips").status_code == 503
    monkeypatch.setenv("RADAR_ADMIN_PASSWORD", "test-admin-long-password")
    monkeypatch.setenv("RADAR_TRAVELER_PASSWORD", "test-traveler-long-password")
    assert client.get("/api/communities").status_code == 401
    assert client.get("/admin").status_code == 401
    assert client.get("/api/trips", auth=("admin", "test-admin-long-password")).status_code == 401
    response = client.get("/api/communities", auth=("admin", "test-admin-long-password"))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert client.delete("/api/communities/1", auth=("admin", "test-admin-long-password"),
                         headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert client.get("/", headers={"Host": "untrusted.example"}).status_code == 400


def test_seed_does_not_overwrite_operator_edits(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "seed.sqlite3"))
    monkeypatch.setenv("RADAR_ADMIN_PASSWORD", "test-admin-long-password")
    client = TestClient(app)
    client.auth = ("admin", "test-admin-long-password")
    assert seed() == 5
    row = client.get("/api/communities").json()["rows"][0]
    assert row["ad_cost_rub"] is None
    assert row["contact_status"] == "new"
    row["leads"] = 3
    assert client.put(f"/api/communities/{row['id']}", json=row).status_code == 200
    assert seed() == 0
    assert client.get("/api/communities").json()["rows"][0]["leads"] == 3
