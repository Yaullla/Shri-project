from fastapi.testclient import TestClient

from radar.web import app

client = TestClient(app)


def test_workspace():
    response = client.get("/")
    assert response.status_code == 200
    assert "Radar" in response.text


def test_api_calculation():
    response = client.post("/api/calculate", json={"purchase_rub": 10000,
        "sale_rub": 20000, "shipping_rub": 1000, "customs_rub": 2000,
        "other_cost_rub": 500, "fee_percent": 12})
    assert response.status_code == 200
    assert response.json()["profit_rub"] == 4100


def test_api_validation():
    assert client.post("/api/calculate", json={"purchase_rub": 1, "sale_rub": 0}).status_code == 422


def test_observations(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "test.sqlite3"))
    assert client.get("/api/observations").json()["rows"] == []
