from fastapi import APIRouter

from neptou_api.llm import generate_optimized_itinerary_anthropic
from neptou_api.schemas import OptimizeRequest

router = APIRouter(prefix="/api", tags=["optimize"])


@router.post("/optimize-itinerary")
async def optimize_itinerary(req: OptimizeRequest) -> dict:
    return await generate_optimized_itinerary_anthropic(req)
