import pytest
from pydantic import BaseModel

from english_app.llm.base import ChatMessage, LLMOutputError
from english_app.llm.providers.fake import FakeProvider, sample_from_schema
from english_app.llm.structured import extract_json, parse_structured, render_prompt
from english_app.modules.conversation.schemas import ConversationSummary, HintList, TurnReply
from english_app.modules.lessons.content import (
    AnswerCheck,
    GrammarLesson,
    PlacementResult,
    VocabularyLesson,
    WritingFeedback,
    WritingTask,
)
from english_app.modules.phrases.schemas import PhraseExplanation
from english_app.modules.review.schemas import SentenceCheck


class Point(BaseModel):
    x: int
    label: str


def test_single_message_is_sent_as_is() -> None:
    assert render_prompt([ChatMessage(role="user", content="Hi")]) == "Hi"


def test_history_is_rendered_as_a_transcript_ending_with_an_instruction() -> None:
    prompt = render_prompt(
        [
            ChatMessage(role="assistant", content="Hello!"),
            ChatMessage(role="user", content="A coffee, please."),
        ]
    )

    assert "Assistant: Hello!" in prompt
    assert "User: A coffee, please." in prompt
    assert prompt.endswith("Output only the reply.")


def test_render_prompt_needs_a_message() -> None:
    with pytest.raises(ValueError):
        render_prompt([])


@pytest.mark.parametrize(
    "text",
    [
        '{"x": 1, "label": "a"}',
        'Sure! ```json\n{"x": 1, "label": "a"}\n``` Hope it helps.',
        'Here you go: {"x": 1, "label": "a"} done',
    ],
)
def test_json_is_found_bare_fenced_or_embedded(text: str) -> None:
    assert parse_structured(text, Point) == Point(x=1, label="a")


def test_missing_or_invalid_json_raises_output_error() -> None:
    with pytest.raises(LLMOutputError):
        extract_json("no json here")
    with pytest.raises(LLMOutputError):
        parse_structured('{"x": "not a number", "label": "a"}', Point)


@pytest.mark.parametrize(
    "schema",
    [
        TurnReply,
        HintList,
        ConversationSummary,
        VocabularyLesson,
        GrammarLesson,
        WritingTask,
        WritingFeedback,
        AnswerCheck,
        PlacementResult,
        PhraseExplanation,
        SentenceCheck,
    ],
)
def test_fake_provider_can_answer_every_schema_the_app_uses(schema: type[BaseModel]) -> None:
    schema.model_validate(sample_from_schema(schema.model_json_schema()))


async def test_fake_provider_uses_registered_replies_and_reports_the_model() -> None:
    provider = FakeProvider()
    provider.register(Point, lambda messages: Point(x=42, label=messages[-1].content))

    result = await provider.complete_structured(
        system="s", messages=[ChatMessage(role="user", content="hi")], schema=Point, model="m"
    )

    assert result.value == Point(x=42, label="hi")
    assert result.model == "m"
