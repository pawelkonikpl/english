from datetime import UTC, datetime

from httpx import AsyncClient

from tests.support import FrozenClock


async def enroll(client: AsyncClient, count: int) -> list[int]:
    phrases = (await client.get("/api/phrases")).json()[:count]
    items = []
    for phrase in phrases:
        response = await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})
        items.append(response.json()["review_item_id"])
    return items


async def dashboard(client: AsyncClient) -> dict:
    return (await client.get("/api/progress/dashboard")).json()


async def test_xp_counts_half_points_and_floors_the_day(client: AsyncClient) -> None:
    items = await enroll(client, 3)  # 3 XP
    for item in items:
        await client.post(f"/api/review/items/{item}/grade", json={"grade": "hard"})  # 1.5 XP

    xp = (await dashboard(client))["xp"]

    assert (xp["today"], xp["total"], xp["goal"]) == (4, 4, 30)


async def test_streak_grows_daily_and_breaks_after_a_missed_day(
    client: AsyncClient, clock: FrozenClock
) -> None:
    await enroll(client, 1)
    clock.advance(days=1)
    await enroll(client, 2)

    same_day = (await dashboard(client))["streak"]
    clock.advance(days=1)
    next_evening = (await dashboard(client))["streak"]
    clock.advance(days=1)
    after_gap = (await dashboard(client))["streak"]

    assert same_day == {"current": 2, "longest": 2, "active_today": True}
    assert next_evening == {"current": 2, "longest": 2, "active_today": False}
    assert after_gap == {"current": 0, "longest": 2, "active_today": False}


async def test_activity_is_bucketed_by_local_day(client: AsyncClient, clock: FrozenClock) -> None:
    clock.set(datetime(2026, 11, 12, 22, 30, tzinfo=UTC))  # 23:30 Warsaw, 12 Nov
    await enroll(client, 1)
    clock.set(datetime(2026, 11, 12, 23, 30, tzinfo=UTC))  # 00:30 Warsaw, 13 Nov

    days = (await client.get("/api/progress/activity", params={"days": 2})).json()

    assert days == [
        {"date": "2026-11-12", "xp": 1, "count": 1},
        {"date": "2026-11-13", "xp": 0, "count": 0},
    ]


async def test_achievements_unlock_once_and_can_be_marked_seen(client: AsyncClient) -> None:
    await enroll(client, 10)

    first = [a["key"] for a in (await dashboard(client))["new_achievements"]]
    await enroll(client, 1)
    still_once = [a["key"] for a in (await dashboard(client))["new_achievements"]]
    seen = await client.post("/api/progress/achievements/seen")
    after = (await dashboard(client))["new_achievements"]
    unlocked = [
        a["key"]
        for a in (await client.get("/api/progress/achievements")).json()
        if a["unlocked_at"]
    ]

    assert first == still_once == ["phrases_10"]
    assert seen.status_code == 204 and after == []
    assert unlocked == ["phrases_10"]


async def test_enrolling_every_tier_one_phrase_unlocks_the_milestone(client: AsyncClient) -> None:
    tier_one = [p for p in (await client.get("/api/phrases")).json() if p["tier"] == "1"]
    for phrase in tier_one:
        await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})

    keys = [a["key"] for a in (await dashboard(client))["new_achievements"]]

    assert len(tier_one) == 31
    assert "phrases_tier_1" in keys


async def test_recommendation_and_item_progress(client: AsyncClient) -> None:
    fresh = (await dashboard(client))["recommendation"]
    await enroll(client, 2)

    data = await dashboard(client)

    assert fresh["target"] == "phrases"
    assert data["recommendation"]["target"] == "review"
    assert data["recommendation"]["reason"].startswith("Masz 2 powtórki")
    assert data["reviews_due"] == 2
    assert data["items"] == [{"item_type": "phrase", "learning": 2, "familiar": 0, "mastered": 0}]
