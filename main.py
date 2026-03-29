from typing import List, Optional
from fastapi import FastAPI, Query
import sqlite3
from llm import (
    generate_answer_anthropic,
    generate_recommendations_anthropic,
    generate_optimized_itinerary_anthropic,
)
from schemas import (
    ChatRequest, ChatResponse,
    RecommendationRequest, PlaceRecommendation,
    SearchRequest, SearchResponse, SearchResult,
    OptimizeRequest,
)
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()  # loads .env into os.environ

# ---------- Models (match your new data structure) ----------


class PlaceLocation(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    geohash: str


class MapSearchResponse(BaseModel):
    count: int
    results: List[PlaceLocation]


# ---------- App ----------

app = FastAPI(title="Neptou AI Backend (Anthropic)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    MAX_TURNS = 20
    history = req.history[-MAX_TURNS:]

    response_text, followups = await generate_answer_anthropic(
        history=history,
        place=req.place_context,
        food=req.food_context,
    )

    return ChatResponse(response=response_text, follow_up_questions=followups)


# ---------- Recommendations ----------

def _get_all_place_names() -> List[str]:
    try:
        conn = sqlite3.connect("places_clean.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM places ORDER BY name")
        names = [row["name"] for row in cursor.fetchall()]
        conn.close()
        return names
    except Exception:
        return []


@app.post("/api/recommendations", response_model=List[PlaceRecommendation])
async def recommendations(req: RecommendationRequest):
    place_names = _get_all_place_names()
    if not place_names:
        return []
    recs = await generate_recommendations_anthropic(req, place_names)
    return recs


# ---------- Search ----------

@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    try:
        conn = sqlite3.connect("places_clean.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query_param = f"%{req.query}%"
        cursor.execute(
            """
            SELECT name, description, geohash
            FROM places
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
            LIMIT ?
            """,
            (query_param, query_param, req.limit),
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        rows = []

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


# ---------- Optimize Itinerary ----------

@app.post("/api/optimize-itinerary")
async def optimize_itinerary(req: OptimizeRequest):
    optimized = await generate_optimized_itinerary_anthropic(req)
    return optimized


# ---------- Map Search (updated to new columns) ----------

@app.get("/api/map/search", response_model=MapSearchResponse)
async def search_places(hash_prefix: str = Query(..., min_length=1)):
    conn = sqlite3.connect("places_clean.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Your table must contain these columns:
    # id, name, description, latitude, longitude, geohash
    query = """
        SELECT id, name, description, latitude, longitude, geohash
        FROM places
        WHERE geohash LIKE ?
    """
    cursor.execute(query, (f"{hash_prefix}%",))
    rows = cursor.fetchall()
    conn.close()

    results: List[PlaceLocation] = []
    for row in rows:
        results.append(
            PlaceLocation(
                id=str(row["id"]),
                name=row["name"],
                description=row["description"],
                latitude=float(
                    row["latitude"]) if row["latitude"] is not None else 0.0,
                longitude=float(
                    row["longitude"]) if row["longitude"] is not None else 0.0,
                geohash=row["geohash"],
            )
        )

    return MapSearchResponse(count=len(results), results=results)
