from typing import List

from fastapi import APIRouter

from neptou_api.database import fetch_all_place_names
from neptou_api.llm import generate_recommendations_anthropic
from neptou_api.schemas import PlaceRecommendation, RecommendationRequest

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommendations", response_model=List[PlaceRecommendation])
async def recommendations(req: RecommendationRequest) -> List[PlaceRecommendation]:
    place_names = fetch_all_place_names()
    if not place_names:
        return []
    return await generate_recommendations_anthropic(req, place_names)
