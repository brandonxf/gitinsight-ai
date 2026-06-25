from fastapi.testclient import TestClient

from app.main import app


def test_root_ok():
    with TestClient(app) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "GitInsight AI"


def test_openapi_available():
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
