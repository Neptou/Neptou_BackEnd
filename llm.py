import os
import json
from typing import List, Optional, Tuple

from anthropic import AsyncAnthropic
from schemas import (
    ChatMessage, PlaceContext, FoodContext,
    RecommendationRequest, PlaceRecommendation,
    OptimizeRequest,
)


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


async def generate_recommendations_anthropic(
    req: RecommendationRequest,
    place_names: List[str],
) -> List[PlaceRecommendation]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    client = AsyncAnthropic(api_key=api_key)

    places_csv = ", ".join(place_names[:80])

    system = (
        "You are Neptou, an AI travel planner for Nepal.\n"
        "Given a traveler profile and a list of available places, recommend the top 7 most relevant places.\n"
        "You MUST output ONLY a valid JSON array (no wrapper object). Each element has keys:\n"
        '  name (string, must match one of the available places exactly),\n'
        '  reason (string, 1-2 sentences),\n'
        '  match_score (float 0-1),\n'
        '  category (string),\n'
        '  is_hidden_gem (bool).\n'
        "No markdown. No extra keys. No extra text.\n"
    )

    user_msg = (
        f"Traveler: {req.name}, style: {req.travel_style}, "
        f"interests: {', '.join(req.interests)}.\n"
    )
    if req.liked_places:
        user_msg += f"Liked places: {', '.join(req.liked_places)}.\n"
    user_msg += f"\nAvailable places: {places_csv}\n\nRecommend 7 places."

    resp = await client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=1200,
        temperature=0.7,
    )

    text_out = "".join(b.text for b in resp.content if b.type == "text")

    try:
        data = _safe_parse_json(text_out)
    except (json.JSONDecodeError, ValueError):
        return []

    if isinstance(data, dict) and "recommendations" in data:
        data = data["recommendations"]
    if not isinstance(data, list):
        return []

    recs: List[PlaceRecommendation] = []
    for item in data[:7]:
        if not isinstance(item, dict) or "name" not in item:
            continue
        recs.append(PlaceRecommendation(
            name=str(item.get("name", "")),
            reason=str(item.get("reason", "Recommended for you")),
            match_score=min(max(float(item.get("match_score", 0.8)), 0.0), 1.0),
            category=str(item.get("category", "")),
            is_hidden_gem=bool(item.get("is_hidden_gem", False)),
        ))
    return recs


async def generate_optimized_itinerary_anthropic(
    req: OptimizeRequest,
) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    client = AsyncAnthropic(api_key=api_key)

    itinerary_json = json.dumps(req.itinerary.model_dump(), indent=2)

    system = (
        "You are Neptou, an AI travel planner for Nepal.\n"
        "Given a trip itinerary, optimize the order of activities to minimize travel time "
        "and maximize the experience. Keep all the same places and days, just reorder activities "
        "within each day and adjust times if needed.\n"
        "You MUST output ONLY valid JSON with keys: name (string), days (array).\n"
        "Each day has: day_number (int), activities (array).\n"
        "Each activity has: place_name (string), notes (string), start_time (string like '9:00 AM'), "
        "end_time (string like '11:00 AM').\n"
        "No markdown. No extra keys. No extra text."
    )

    resp = await client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": f"Optimize this itinerary:\n{itinerary_json}"}],
        max_tokens=2000,
        temperature=0.5,
    )

    text_out = "".join(b.text for b in resp.content if b.type == "text")

    try:
        data = _safe_parse_json(text_out)
    except (json.JSONDecodeError, ValueError):
        return req.itinerary.model_dump()

    if not isinstance(data, dict) or "days" not in data:
        return req.itinerary.model_dump()

    return data
