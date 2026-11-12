from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from english_app.core.config import Settings
from english_app.core.errors import ConfigurationError, register_error_handlers
from english_app.main import create_app, mount_frontend
from tests.support import FrozenClock, RecordingProvider, serve


async def test_all_modules_are_enabled_by_default(client: AsyncClient) -> None:
    keys = [m["key"] for m in (await client.get("/api/modules")).json()]

    assert keys == ["progress", "phrases", "review", "conversation", "lessons", "profile"]


async def test_disabled_module_disappears_from_api(
    settings: Settings, provider: RecordingProvider, clock: FrozenClock
) -> None:
    settings.enabled_modules = ["profile", "review", "phrases", "progress"]
    app = create_app(settings, llm_provider=provider, clock=clock)
    async with serve(app) as client:
        keys = [m["key"] for m in (await client.get("/api/modules")).json()]
        scenarios = await client.get("/api/conversation/scenarios")
        lessons = await client.get("/api/lessons")
        phrases = await client.get("/api/phrases/sections")

    assert "conversation" not in keys and "lessons" not in keys
    assert scenarios.status_code == lessons.status_code == 404
    assert scenarios.json() == {"error": {"code": "not_found", "message": "Nie znaleziono."}}
    assert phrases.status_code == 200


def test_module_without_its_dependency_stops_startup(settings: Settings) -> None:
    settings.enabled_modules = ["conversation"]

    with pytest.raises(ConfigurationError, match="requires"):
        create_app(settings, llm_provider=RecordingProvider())


def test_unknown_provider_stops_startup(settings: Settings) -> None:
    settings.llm_provider = "nope"

    with pytest.raises(ConfigurationError, match="Unknown LLM_PROVIDER"):
        create_app(settings)


@pytest.fixture
def frontend_app(tmp_path: Path) -> FastAPI:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "main.js").write_text("console.log('hi')")
    (tmp_path / "secret.txt").write_text("secret")
    app = FastAPI()

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    register_error_handlers(app)
    mount_frontend(app, dist)
    return app


@pytest.mark.parametrize("path", ["/", "/phrases/1.1", "/settings"])
async def test_spa_routes_return_index(frontend_app: FastAPI, path: str) -> None:
    async with AsyncClient(transport=ASGITransport(app=frontend_app), base_url="http://t") as c:
        response = await c.get(path)

    assert response.status_code == 200 and response.text == "<html>app</html>"


async def test_assets_api_and_traversal(frontend_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=frontend_app), base_url="http://t") as c:
        asset = await c.get("/assets/main.js")
        api_ok = await c.get("/api/health")
        api_missing = await c.get("/api/unknown")
        traversal = await c.get("/%2e%2e/secret.txt")

    assert asset.text == "console.log('hi')"
    assert api_ok.json() == {"status": "ok"}
    assert api_missing.status_code == 404 and api_missing.json()["error"]["code"] == "not_found"
    assert "secret" not in traversal.text


def test_missing_build_serves_api_only(tmp_path: Path) -> None:
    app = FastAPI()
    mount_frontend(app, tmp_path / "nothing")

    assert [r.path for r in app.routes if getattr(r, "path", "").startswith("/{")] == []
