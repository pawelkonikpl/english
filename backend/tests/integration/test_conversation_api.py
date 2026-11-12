import pytest
from httpx import AsyncClient

from english_app.llm.base import LLMTimeoutError
from english_app.modules.conversation.schemas import (
    ConversationSummary,
    Correction,
    SuggestedPhrase,
    TurnReply,
)
from tests.support import RecordingProvider


@pytest.fixture(autouse=True)
def realistic_replies(provider: RecordingProvider) -> None:
    provider.register(
        TurnReply,
        lambda messages: TurnReply(
            reply="Sure! Anything else?",
            corrections=[
                Correction(original="I want", corrected="Could I get", explanation="Grzeczniej.")
            ],
            better_alternatives=["Could I get a coffee, please?"],
            used_target_phrases=[],
        ),
    )
    provider.register(
        ConversationSummary,
        lambda messages: ConversationSummary(
            score=7,
            strengths=["Dobre pytania"],
            mistakes=[],
            new_phrases=[SuggestedPhrase(english="Could I get a latte?", polish="Poproszę latte")],
        ),
    )


async def start(client: AsyncClient, **payload) -> dict:
    response = await client.post(
        "/api/conversation", json={"scenario_key": "coffee_shop", **payload}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_start_saves_the_opening_line_and_target_phrases(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    conversation = await start(client, target_phrase_ids=[1, 2, 99999])

    assert [m["role"] for m in conversation["messages"]] == ["assistant"]
    assert conversation["messages"][0]["model"] == "fake-main"
    assert [p["id"] for p in conversation["target_phrases"]] == [1, 2]
    system = provider.systems_for("text")[0]
    assert "a friendly barista" in system
    assert "Sorry, could you say that again?" in system


async def test_unknown_scenario_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/conversation", json={"scenario_key": "moon"})

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Nieznana scenka."


async def test_reply_stores_feedback_and_model(client: AsyncClient) -> None:
    conversation = await start(client)

    response = await client.post(
        f"/api/conversation/{conversation['id']}/messages", json={"content": "I want a coffee"}
    )
    stored = (await client.get(f"/api/conversation/{conversation['id']}")).json()

    body = response.json()
    assert body["user_message"]["feedback"]["corrections"][0]["corrected"] == "Could I get"
    assert body["assistant_message"]["content"] == "Sure! Anything else?"
    assert body["assistant_message"]["model"] == "fake-main"
    assert [m["role"] for m in stored["messages"]] == ["assistant", "user", "assistant"]


async def test_failed_model_call_leaves_no_half_saved_turn(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    conversation = await start(client)
    provider.fail_with = LLMTimeoutError("slow")

    response = await client.post(
        f"/api/conversation/{conversation['id']}/messages", json={"content": "Hello"}
    )
    stored = (await client.get(f"/api/conversation/{conversation['id']}")).json()

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "llm_timeout"
    assert len(stored["messages"]) == 1


async def test_history_is_sent_to_the_model(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    conversation = await start(client)
    await client.post(f"/api/conversation/{conversation['id']}/messages", json={"content": "Hi"})

    await client.post(f"/api/conversation/{conversation['id']}/messages", json={"content": "Bye"})

    _, _, messages = [p for p in provider.prompts if p[0] == "TurnReply"][-1]
    assert [(m.role, m.content) for m in messages][-3:] == [
        ("user", "Hi"),
        ("assistant", "Sure! Anything else?"),
        ("user", "Bye"),
    ]


async def test_hint_uses_the_fast_model(client: AsyncClient, provider: RecordingProvider) -> None:
    await client.put("/api/llm/settings", json={"main": "fake-main", "fast": "fake-fast"})
    conversation = await start(client)

    hints = await client.post(f"/api/conversation/{conversation['id']}/hint")

    assert hints.status_code == 200
    assert provider.calls_for("HintList") == ["fake-fast"]


async def test_finish_scores_once_and_awards_xp(client: AsyncClient) -> None:
    conversation = await start(client)
    cid = conversation["id"]
    await client.post(f"/api/conversation/{cid}/messages", json={"content": "I want a coffee"})

    finished = (await client.post(f"/api/conversation/{cid}/finish")).json()
    again = (await client.post(f"/api/conversation/{cid}/finish")).json()
    late = await client.post(f"/api/conversation/{cid}/messages", json={"content": "Hello?"})
    dashboard = (await client.get("/api/progress/dashboard")).json()

    assert (finished["status"], finished["score"]) == ("finished", 7)
    assert again["score"] == 7
    assert late.status_code == 409
    assert dashboard["xp"]["today"] == 7
    assert "first_conversation" in [a["key"] for a in dashboard["new_achievements"]]


async def test_finish_needs_a_learner_message(client: AsyncClient) -> None:
    conversation = await start(client)

    response = await client.post(f"/api/conversation/{conversation['id']}/finish")

    assert response.status_code == 422


async def test_suggested_phrase_goes_to_reviews_once(client: AsyncClient) -> None:
    conversation = await start(client)
    url = f"/api/conversation/{conversation['id']}/phrases"
    payload = {"english": "Could I get a latte?", "polish": "Poproszę latte"}

    first = (await client.post(url, json=payload)).json()
    second = (await client.post(url, json=payload)).json()
    sections = (await client.get("/api/phrases/sections")).json()

    assert first["newly_enrolled"] is True and second["newly_enrolled"] is False
    assert first["phrase_id"] == second["phrase_id"]
    ai = [s for s in sections if s["tier"] == "ai"]
    assert ai == [
        {
            "tier": "ai",
            "tier_title": "Z rozmów i lekcji z AI",
            "code": "AI.1",
            "title": "Frazy podsunięte przez AI",
            "total": 1,
            "learning": 1,
            "mastered": 0,
        }
    ]


async def test_recent_conversations_list(client: AsyncClient) -> None:
    await start(client)

    listed = (await client.get("/api/conversation")).json()

    assert [(c["title"], c["status"], c["messages"]) for c in listed] == [
        ("W kawiarni", "active", 1)
    ]
