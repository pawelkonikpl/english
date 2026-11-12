from httpx import AsyncClient


async def test_first_read_persists_defaults(client: AsyncClient) -> None:
    first = (await client.get("/api/profile")).json()
    second = (await client.get("/api/profile")).json()

    assert first == second
    assert (first["level"], first["native_language"], first["onboarding_done"]) == (
        "A2",
        "pl",
        False,
    )


async def test_partial_update_keeps_other_fields(client: AsyncClient) -> None:
    await client.put("/api/profile", json={"display_name": "Ola", "goals": ["Podróże"]})

    updated = (
        await client.put("/api/profile", json={"level": "B1", "onboarding_done": True})
    ).json()

    assert updated["display_name"] == "Ola"
    assert updated["goals"] == ["Podróże"]
    assert (updated["level"], updated["onboarding_done"]) == ("B1", True)


async def test_display_name_can_be_cleared(client: AsyncClient) -> None:
    await client.put("/api/profile", json={"display_name": "Ola"})

    updated = (await client.put("/api/profile", json={"display_name": None})).json()

    assert updated["display_name"] is None


async def test_invalid_values_are_rejected(client: AsyncClient) -> None:
    level = await client.put("/api/profile", json={"level": "D1"})
    goal = await client.put("/api/profile", json={"daily_goal_xp": 1})

    assert level.status_code == goal.status_code == 422
