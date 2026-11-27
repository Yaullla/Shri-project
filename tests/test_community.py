from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from radar.web import app


def test_crm_crud(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "crm.sqlite3"))
    client = TestClient(app)
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
    client = TestClient(app)
    body = {"origin": "Delhi", "destination": "Moscow",
            "departure": (datetime.now(UTC).date() + timedelta(days=1)).isoformat(),
            "capacity_kg": 2, "reward_rub": 1000}
    result = client.post("/api/trips", json=body)
    assert result.status_code == 201
    assert len(client.get("/api/trips").json()["rows"]) == 1
    assert client.post("/api/trips", json=body | {"capacity_kg": 51}).status_code == 422
    assert client.delete(f"/api/trips/{result.json()['id']}").status_code == 200
    assert client.get("/travel").status_code == 200
    assert client.get("/admin").status_code == 200
