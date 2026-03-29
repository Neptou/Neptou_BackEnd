from typing import List

from fastapi import APIRouter, Query

from neptou_api.database import fetch_places_by_geohash_prefix
from neptou_api.schemas import MapSearchResponse, PlaceLocation

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/search", response_model=MapSearchResponse)
async def search_places(hash_prefix: str = Query(..., min_length=1)) -> MapSearchResponse:
    rows = fetch_places_by_geohash_prefix(hash_prefix)

    results: List[PlaceLocation] = []
    for row in rows:
        results.append(
            PlaceLocation(
                id=str(row["id"]),
                name=row["name"],
                description=row["description"],
                latitude=float(row["latitude"]) if row["latitude"] is not None else 0.0,
                longitude=float(row["longitude"]) if row["longitude"] is not None else 0.0,
                geohash=row["geohash"],
            )
        )

    return MapSearchResponse(count=len(results), results=results)
