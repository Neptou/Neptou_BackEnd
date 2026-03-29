from fastapi import APIRouter

from neptou_api.database import search_places_text
from neptou_api.schemas import SearchRequest, SearchResponse, SearchResult

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    rows = search_places_text(req.query, req.limit)
    results = [
        SearchResult(
            name=row["name"],
            category="",
            area="",
            similarity_score=0.8,
        )
        for row in rows
    ]
    return SearchResponse(results=results)
