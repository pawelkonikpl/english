"""Helpers shared by providers: transcript rendering and JSON parsing fallback."""

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from english_app.llm.base import ChatMessage, LLMOutputError, SchemaT

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def render_prompt(messages: Sequence[ChatMessage]) -> str:
    """Turn the conversation into one prompt for SDKs that take a single user turn."""
    if not messages:
        raise ValueError("At least one message is required")
    if len(messages) == 1:
        return messages[0].content

    lines = ["Conversation so far:", ""]
    for message in messages:
        speaker = "User" if message.role == "user" else "Assistant"
        lines.append(f"{speaker}: {message.content}")
        lines.append("")
    lines.append("Reply as the Assistant to the last User message. Output only the reply.")
    return "\n".join(lines)


def schema_instruction(schema: type[BaseModel]) -> str:
    """Instruction appended to the system prompt when the SDK has no native JSON mode."""
    return (
        "Respond with a single JSON object and nothing else. "
        "It must validate against this JSON Schema:\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )


def extract_json(text: str) -> str:
    """Return the JSON object embedded in a model reply (bare or inside a code fence)."""
    fenced = _JSON_FENCE.search(text)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end < start:
        raise LLMOutputError("No JSON object found in model output")
    return candidate[start : end + 1]


def parse_structured(text: str, schema: type[SchemaT]) -> SchemaT:
    """Parse and validate a model reply.

    Raises:
        LLMOutputError: no JSON object, or it does not match `schema`.
    """
    try:
        return schema.model_validate_json(extract_json(text))
    except ValidationError as exc:
        raise LLMOutputError(f"Model output does not match {schema.__name__}: {exc}") from exc


def validation_feedback(error: LLMOutputError) -> str:
    """Message sent back to the model when its first structured reply was invalid."""
    return (
        "Your previous reply was not valid JSON for the required schema. "
        f"Error: {error}. Reply again with only the corrected JSON object."
    )
