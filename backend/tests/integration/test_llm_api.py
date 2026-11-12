from httpx import AsyncClient

from english_app.core.config import Settings
from english_app.main import create_app
from tests.support import FrozenClock, RecordingProvider, serve


async def test_status_reports_provider_and_effective_models(client: AsyncClient) -> None:
    status = (await client.get("/api/llm/status")).json()

    assert status["provider"] == "fake"
    assert status["available"] is True
    assert status["models"] == {"main": None, "fast": None}


async def test_models_endpoint_lists_provider_models(client: AsyncClient) -> None:
    ids = [m["id"] for m in (await client.get("/api/llm/models")).json()]

    assert ids == ["fake-main", "fake-fast"]


async def test_override_takes_effect_for_the_next_call_without_restart(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    await client.put("/api/llm/settings", json={"fast": "fake-fast"})
    review_id = await enrolled_review_item(client)

    response = await client.post(
        f"/api/review/items/{review_id}/check-sentence", json={"sentence": "Sorry, again?"}
    )

    assert response.json()["model"] == "fake-fast"
    assert provider.calls_for("SentenceCheck") == ["fake-fast"]


async def test_fast_tier_falls_back_to_main_override(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    await client.put("/api/llm/settings", json={"main": "fake-main"})

    settings = (await client.get("/api/llm/settings")).json()

    assert [(t["tier"], t["effective"]) for t in settings["tiers"]] == [
        ("main", "fake-main"),
        ("fast", "fake-main"),
    ]


async def test_unknown_model_needs_allow_custom(client: AsyncClient) -> None:
    rejected = await client.put("/api/llm/settings", json={"main": "gpt-9"})
    accepted = await client.put("/api/llm/settings", json={"main": "gpt-9", "allow_custom": True})

    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "invalid_input"
    assert "gpt-9" in rejected.json()["error"]["message"]
    assert accepted.status_code == 200
    assert accepted.json()["tiers"][0]["effective"] == "gpt-9"


async def test_null_removes_override_and_omitted_tier_is_unchanged(client: AsyncClient) -> None:
    await client.put("/api/llm/settings", json={"main": "fake-main", "fast": "fake-fast"})

    response = await client.put("/api/llm/settings", json={"main": None})

    tiers = {t["tier"]: t for t in response.json()["tiers"]}
    assert tiers["main"]["override"] is None
    assert tiers["fast"]["override"] == "fake-fast"


async def test_override_survives_restart(
    settings: Settings, provider: RecordingProvider, clock: FrozenClock
) -> None:

    first = create_app(settings, llm_provider=provider, clock=clock)
    async with serve(first) as c:
        await c.put("/api/llm/settings", json={"fast": "fake-fast"})

    second = create_app(settings, llm_provider=RecordingProvider(), clock=clock)
    async with serve(second) as c:
        status = (await c.get("/api/llm/status")).json()

    assert status["models"]["fast"] == "fake-fast"


async def test_test_call_reports_model_and_rejects_two_targets(client: AsyncClient) -> None:
    ok = await client.post("/api/llm/test", json={"model": "fake-fast"})
    both = await client.post("/api/llm/test", json={"tier": "main", "model": "x"})

    assert ok.json()["ok"] is True and ok.json()["model"] == "fake-fast"
    assert both.status_code == 422
    assert both.json()["error"]["code"] == "invalid_input"


async def test_failing_model_is_reported_by_the_test_call(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    from english_app.llm.base import LLMUnavailableError

    provider.fail_with = LLMUnavailableError("down", user_message="Zaloguj się")

    result = (await client.post("/api/llm/test", json={"tier": "main"})).json()

    assert result["ok"] is False and result["detail"] == "Zaloguj się"


async def enrolled_review_item(client: AsyncClient) -> int:
    phrase = (await client.get("/api/phrases/learn-session")).json()["phrases"][0]
    enrolled = await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})
    return int(enrolled.json()["review_item_id"])
