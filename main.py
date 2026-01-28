from typing import List, Optional
from fastapi import FastAPI, Query
import geohash as pgh
import re
import sqlite3
from llm import generate_answer_anthropic
from schemas import ChatRequest, ChatResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import List, Optional


class ParkLocation(BaseModel):
    name: str
    description: Optional[str] = None
    lat: float
    lng: float
    geohash: str


class MapSearchResponse(BaseModel):
    count: int
    results: List[ParkLocation]


load_dotenv()  # loads .env into os.environ


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

    print(req)

    response_text, followups = await generate_answer_anthropic(
        history=history,
        place=req.place_context,
        food=req.food_context,
    )

    return ChatResponse(response=response_text, follow_up_questions=followups)

    # response_text = "Received your message."
    # print(req)

    # return ChatResponse(response=response_text, follow_up_questions=[])


def parse_wkt(wkt_string: str):
    """Extracts floats from Point(Lon Lat) format."""
    # Note: Wikidata/WKT uses (Longitude Latitude)
    match = re.findall(r"[-+]?\d*\.\d+|\d+", wkt_string)
    if len(match) >= 2:
        return float(match[1]), float(match[0])  # Returns (Lat, Lng)
    return 0.0, 0.0


@app.get("/api/map/search", response_model=MapSearchResponse)
async def search_parks(hash_prefix: str = Query(..., min_length=1)):
    conn = sqlite3.connect('places.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Optimized prefix search
    query = "SELECT parkLabel, parkDescription, coord, geohash FROM places WHERE geohash LIKE ?"
    cursor.execute(query, (f"{hash_prefix}%",))

    rows = cursor.fetchall()
    conn.close()

    park_list = []
    for row in rows:
        lat, lng = parse_wkt(row['coord'])

        # Instantiate the Pydantic model
        park_list.append(ParkLocation(
            name=row['parkLabel'],
            description=row['parkDescription'],
            lat=lat,
            lng=lng,
            geohash=row['geohash']
        ))

    return MapSearchResponse(count=len(park_list), results=park_list)
