import os
import json
from typing import List, Optional, Tuple

from anthropic import AsyncAnthropic
from schemas import ChatMessage, PlaceContext, FoodContext


def build_system_prompt(place: Optional[PlaceContext], food: Optional[FoodContext]) -> str:
    base = (
        "You are Neptou, a helpful AI travel companion focused on Nepal.\n"
        "Be concise, friendly, and practical.\n"
        "When you answer, also suggest 3 short related follow-up questions.\n"
        "You MUST output ONLY valid JSON with keys: response (string), follow_up_questions (array of strings).\n"
        "No markdown. No extra keys. No extra text."
    )

    if place:
        base += "\n\nPlace context:\n"
        base += f"- name: {place.name}\n"
        base += f"- description: {place.description or ''}\n"
        base += f"- category: {place.category or ''}\n"
        base += f"- name_nepali: {place.name_nepali or ''}\n"
        if place.tips:
            base += f"- tips: {', '.join(place.tips)}\n"

    if food:
        base += "\n\nFood context:\n"
        base += f"- name: {food.name}\n"
        base += f"- description: {food.description or ''}\n"
        base += f"- category: {food.category or ''}\n"

    return base


def to_anthropic_messages(history: List[ChatMessage]) -> List[dict]:
    """
    Anthropic Messages API uses roles: 'user' and 'assistant'.
    We'll pass your history through directly.
    """
    return [{"role": m.role, "content": m.content} for m in history]


def _safe_parse_json(text: str) -> dict:
    """
    Claude usually obeys JSON-only if prompted, but this adds a safety net.
    """
    text = text.strip()

    # If it wrapped JSON in accidental fences, strip them
    if text.startswith("```"):
        text = text.strip("`")
        # after stripping, it might still contain a language tag
        lines = text.splitlines()
        if lines and lines[0].lower().startswith("json"):
            text = "\n".join(lines[1:]).strip()

    return json.loads(text)


async def generate_answer_anthropic(
    history: List[ChatMessage],
    place: Optional[PlaceContext],
    food: Optional[FoodContext],
) -> Tuple[str, List[str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    client = AsyncAnthropic(api_key=api_key)

    system = build_system_prompt(place, food)
    messages = to_anthropic_messages(history)

    resp = await client.messages.create(
        model=model,
        system=system,
        messages=messages,
        max_tokens=800,
        temperature=0.7,
    )

    # Anthropic returns content blocks; we want the combined text
    text_out = ""
    for block in resp.content:
        if block.type == "text":
            text_out += block.text

    data = _safe_parse_json(text_out)

    response_text = str(data.get("response", "")).strip()
    followups = data.get("follow_up_questions") or []
    followups = [str(x).strip() for x in followups if str(x).strip()]

    # Final fallback
    if not response_text:
        response_text = "Sorry — I couldn’t generate a response right now."

    return response_text, followups[:5]
