from datetime import date, timedelta

from httpx import AsyncClient

from english_app.core.config import Settings
from english_app.main import create_app
from tests.support import FrozenClock, RecordingProvider, serve


async def learn_session(client: AsyncClient) -> dict:
    return (await client.get("/api/phrases/learn-session")).json()


async def test_all_seed_phrases_are_loaded_once_across_restarts(
    client: AsyncClient, settings: Settings, clock: FrozenClock
) -> None:
    before = sum(s["total"] for s in (await client.get("/api/phrases/sections")).json())

    again = create_app(settings, llm_provider=RecordingProvider(), clock=clock)
    async with serve(again) as c:
        sections = (await c.get("/api/phrases/sections")).json()

    assert before == sum(s["total"] for s in sections) == 239
    assert len(sections) == 19


async def test_learn_session_follows_course_order_and_daily_limit(client: AsyncClient) -> None:
    session = await learn_session(client)

    assert session["daily_limit"] == session["remaining_today"] == 10
    assert [p["section_code"] for p in session["phrases"]] == ["1.1"] * 10
    assert session["phrases"][0]["english"] == "Sorry, could you say that again?"


async def test_limit_counts_enrolments_of_the_day(client: AsyncClient) -> None:
    for phrase in (await learn_session(client))["phrases"][:4]:
        await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})

    session = await learn_session(client)

    assert session["remaining_today"] == len(session["phrases"]) == 6


async def test_limit_resets_at_local_midnight(client: AsyncClient, clock: FrozenClock) -> None:
    from datetime import UTC, datetime

    clock.set(datetime(2026, 11, 12, 22, 30, tzinfo=UTC))  # 23:30 in Warsaw
    for phrase in (await learn_session(client))["phrases"][:10]:
        await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})
    assert (await learn_session(client))["remaining_today"] == 0

    clock.set(datetime(2026, 11, 12, 23, 30, tzinfo=UTC))  # 00:30 next day in Warsaw

    assert (await learn_session(client))["remaining_today"] == 10


async def test_enroll_is_idempotent_and_known_phrases_wait_three_days(
    client: AsyncClient, clock: FrozenClock
) -> None:
    phrase_id = (await learn_session(client))["phrases"][0]["id"]

    first = (await client.post(f"/api/phrases/{phrase_id}/enroll", json={"known": True})).json()
    second = (await client.post(f"/api/phrases/{phrase_id}/enroll", json={})).json()
    listed = (await client.get("/api/phrases", params={"section": "1.1"})).json()

    assert first["newly_enrolled"] is True and second["newly_enrolled"] is False
    assert first["review_item_id"] == second["review_item_id"]
    entry = next(p for p in listed if p["id"] == phrase_id)
    assert entry["status"] == "learning"
    assert date.fromisoformat(entry["due_on"]) == clock.today() + timedelta(days=3)


async def test_status_filter(client: AsyncClient) -> None:
    phrase_id = (await learn_session(client))["phrases"][0]["id"]
    await client.post(f"/api/phrases/{phrase_id}/enroll", json={})

    learning = (await client.get("/api/phrases", params={"status": "learning"})).json()

    assert [p["id"] for p in learning] == [phrase_id]


async def test_explanation_is_generated_once_then_cached(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    phrase_id = (await learn_session(client))["phrases"][0]["id"]

    first = (await client.post(f"/api/phrases/{phrase_id}/explain", json={})).json()
    second = (await client.post(f"/api/phrases/{phrase_id}/explain", json={})).json()
    regenerated = (
        await client.post(f"/api/phrases/{phrase_id}/explain", json={"regenerate": True})
    ).json()

    assert (first["cached"], second["cached"], regenerated["cached"]) == (False, True, False)
    assert len(provider.calls_for("PhraseExplanation")) == 2
    assert second["model"] == "fake-main"


async def test_unknown_phrase_returns_polish_404(client: AsyncClient) -> None:
    response = await client.post("/api/phrases/99999/enroll", json={})

    assert response.status_code == 404
    assert response.json()["error"] == {"code": "not_found", "message": "Nie znaleziono frazy."}
