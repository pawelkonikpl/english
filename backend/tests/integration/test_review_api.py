from datetime import date

from httpx import AsyncClient

from tests.support import FrozenClock


async def enroll_first(client: AsyncClient, count: int = 1) -> list[int]:
    phrases = (await client.get("/api/phrases/learn-session")).json()["phrases"][:count]
    ids = []
    for phrase in phrases:
        response = await client.post(f"/api/phrases/{phrase['id']}/enroll", json={})
        ids.append(response.json()["review_item_id"])
    return ids


async def grade(client: AsyncClient, item_id: int, value: str, mode: str = "recognition") -> dict:
    response = await client.post(
        f"/api/review/items/{item_id}/grade", json={"grade": value, "mode": mode}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_due_cards_carry_phrase_content(client: AsyncClient) -> None:
    await enroll_first(client, 2)

    due = (await client.get("/api/review/due")).json()

    assert [d["card"]["front"] for d in due] == [
        "Sorry, could you say that again?",
        "Could you speak a bit more slowly, please?",
    ]
    assert due[0]["card"]["back"] == "Przepraszam, możesz powtórzyć?"
    assert due[0]["card"]["label"] == "Gdy czegoś nie rozumiesz"


async def test_three_good_reviews_on_schedule_lead_to_a_week(
    client: AsyncClient, clock: FrozenClock
) -> None:
    [item] = await enroll_first(client)

    intervals = []
    for _ in range(3):
        result = await grade(client, item, "good")
        intervals.append(result["interval_days"])
        clock.advance(days=result["interval_days"])

    assert intervals == [1, 3, 7]
    assert result["mastery"] == 2


async def test_again_keeps_the_card_due_today(client: AsyncClient, clock: FrozenClock) -> None:
    [item] = await enroll_first(client)

    result = await grade(client, item, "again")
    due_ids = [d["id"] for d in (await client.get("/api/review/due")).json()]

    assert result["due_again_today"] is True
    assert date.fromisoformat(result["due_on"]) == clock.today()
    assert item in due_ids


async def test_graded_card_leaves_todays_queue(client: AsyncClient) -> None:
    [item] = await enroll_first(client)

    await grade(client, item, "good")

    assert (await client.get("/api/review/due")).json() == []
    assert (await client.get("/api/review/summary")).json() == {"due_today": 0, "total_reviews": 1}


async def test_recall_check_is_tolerant(client: AsyncClient) -> None:
    [item] = await enroll_first(client)

    typo = await client.post(
        f"/api/review/items/{item}/check-recall", json={"answer": "sorry could you say that agian"}
    )
    wrong = await client.post(f"/api/review/items/{item}/check-recall", json={"answer": "hello"})

    assert typo.json() == {"correct": True, "expected": "Sorry, could you say that again?"}
    assert wrong.json()["correct"] is False


async def test_sentence_check_uses_the_fast_model(client: AsyncClient, provider) -> None:
    [item] = await enroll_first(client)
    await client.put("/api/llm/settings", json={"main": "fake-main", "fast": "fake-fast"})

    await client.post(f"/api/review/items/{item}/check-sentence", json={"sentence": "Sorry?"})

    assert provider.calls_for("SentenceCheck") == ["fake-fast"]


async def test_invalid_grade_and_unknown_item(client: AsyncClient) -> None:
    [item] = await enroll_first(client)

    invalid = await client.post(f"/api/review/items/{item}/grade", json={"grade": "meh"})
    missing = await client.post("/api/review/items/999/grade", json={"grade": "good"})

    assert invalid.status_code == 422 and invalid.json()["error"]["code"] == "invalid_input"
    assert missing.status_code == 404
