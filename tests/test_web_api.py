import os
import asyncio
from pathlib import Path
import tomllib

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ.pop("CORS_ORIGINS", None)

import pytest
import httpx
from sqlalchemy.exc import SQLAlchemyError

from backend.routers.database import Base, engine, get_db
from backend.routers.main import app


VALID_GROUP = {
    "id": "g-test",
    "name": "Nhóm kiểm thử",
    "members": ["An", "Bình"],
    "balances": {"An": 50000, "Bình": -50000},
    "expenses": [
        {
            "title": "Bữa trưa",
            "amount": 100000,
            "payer": "An",
            "participants": ["An", "Bình"],
        }
    ],
}


@pytest.fixture()
def client():
    # This is an isolated in-memory database, never the configured Neon URL.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    class ASGITestClient:
        def request(self, method, url, **kwargs):
            async def send():
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport,
                    base_url="http://testserver",
                ) as async_client:
                    return await async_client.request(method, url, **kwargs)

            return asyncio.run(send())

        def get(self, url, **kwargs):
            return self.request("GET", url, **kwargs)

        def put(self, url, **kwargs):
            return self.request("PUT", url, **kwargs)

        def post(self, url, **kwargs):
            return self.request("POST", url, **kwargs)

        def delete(self, url, **kwargs):
            return self.request("DELETE", url, **kwargs)

    yield ASGITestClient()


def put_state(client, expected_version: int, groups=None):
    return client.put(
        "/api/demo/state",
        json={
            "expected_version": expected_version,
            "data": {"groups": [VALID_GROUP] if groups is None else groups},
        },
    )


def test_frontend_and_assets_are_served_from_same_app(client):
    page = client.get("/")
    script = client.get("/app.js")
    stylesheet = client.get("/styles.css")

    assert page.status_code == 200
    assert "Quản lý Chi tiêu Nhóm" in page.text
    assert script.status_code == 200
    assert 'const API_BASE_URL = ""' in script.text
    assert "127.0.0.1" not in script.text
    assert stylesheet.status_code == 200


def test_vercel_uses_one_custom_entrypoint_and_keeps_routing_in_fastapi():
    project_root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["tool"]["vercel"]["entrypoint"] == "backend.routers.main:app"
    assert config["tool"]["vercel"]["fastapi"]["static"]["cdn"] is False
    assert not (project_root / "index.py").exists()


def test_openapi_exposes_public_api_routes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/demo/state" in paths
    assert "/api/items/" in paths


def test_health_and_existing_items_route_are_preserved(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    items_response = client.get("/api/items/")
    assert items_response.status_code == 200
    assert items_response.json() == []


def test_existing_items_crud_routes_are_preserved(client):
    created = client.post(
        "/api/items/",
        json={"name": "Bút thử", "description": "Kiểm tra", "price": 12000},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    loaded = client.get(f"/api/items/{item_id}")
    assert loaded.status_code == 200
    assert loaded.json()["name"] == "Bút thử"

    deleted = client.delete(f"/api/items/{item_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/items/{item_id}").status_code == 404


def test_get_empty_state_does_not_create_a_record(client):
    first = client.get("/api/demo/state")
    second = client.get("/api/demo/state")

    assert first.status_code == 200
    assert first.json() == {
        "id": 1,
        "version": 0,
        "data": {"groups": []},
        "updated_at": None,
    }
    assert second.json()["version"] == 0


def test_initial_put_persists_and_can_be_loaded_again(client):
    created = put_state(client, expected_version=0)
    loaded = client.get("/api/demo/state")

    assert created.status_code == 200
    assert created.json()["version"] == 1
    assert loaded.status_code == 200
    assert loaded.json()["data"]["groups"][0]["name"] == "Nhóm kiểm thử"


def test_occ_update_and_stale_version_conflict(client):
    assert put_state(client, expected_version=0).json()["version"] == 1
    updated = put_state(client, expected_version=1, groups=[])
    stale = put_state(client, expected_version=1)

    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "VERSION_CONFLICT"
    assert stale.json()["detail"]["current_version"] == 2


def test_expected_positive_version_never_inserts_missing_record(client):
    response = put_state(client, expected_version=7)

    assert response.status_code == 409
    assert response.json()["detail"]["current_version"] == 0
    assert client.get("/api/demo/state").json()["version"] == 0


def test_second_initial_writer_receives_conflict(client):
    assert put_state(client, expected_version=0).status_code == 200
    conflict = put_state(client, expected_version=0)

    assert conflict.status_code == 409
    assert conflict.json()["detail"]["current_version"] == 1


def test_invalid_group_reference_returns_422_without_writing(client):
    invalid_group = {
        **VALID_GROUP,
        "expenses": [{**VALID_GROUP["expenses"][0], "payer": "Người lạ"}],
    }
    response = put_state(client, expected_version=0, groups=[invalid_group])

    assert response.status_code == 422
    assert client.get("/api/demo/state").json()["version"] == 0


def test_cors_is_not_open_by_default(client):
    response = client.get(
        "/api/demo/state",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_database_error_returns_generic_500_and_rolls_back(client):
    class FailingSession:
        rolled_back = False

        def execute(self, _statement):
            raise SQLAlchemyError("sensitive database diagnostic")

        def rollback(self):
            self.rolled_back = True

    failing_session = FailingSession()

    def override_db():
        yield failing_session

    app.dependency_overrides[get_db] = override_db
    try:
        response = put_state(client, expected_version=1)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Lỗi hệ thống khi lưu trữ trạng thái demo."}
    assert "sensitive" not in response.text
    assert failing_session.rolled_back is True
