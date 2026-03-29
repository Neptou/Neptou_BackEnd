from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class PlaceContext(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    name_nepali: Optional[str] = None
    tips: Optional[List[str]] = None


class FoodContext(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class ChatRequest(BaseModel):
    history: List[ChatMessage] = Field(min_length=1)
    place_context: Optional[PlaceContext] = None
    food_context: Optional[FoodContext] = None


class ChatResponse(BaseModel):
    response: str
    follow_up_questions: List[str] = Field(default_factory=list)


# --- Recommendations ---

class RecommendationRequest(BaseModel):
    name: str = ""
    travel_style: str = "Mixed"
    interests: List[str] = Field(default_factory=list)
    liked_places: List[str] = Field(default_factory=list)


class PlaceRecommendation(BaseModel):
    name: str
    reason: str
    match_score: float
    category: str
    is_hidden_gem: bool = False


# --- Search ---

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    name: str
    category: str = ""
    area: str = ""
    similarity_score: float = 0.0


class SearchResponse(BaseModel):
    results: List[SearchResult]


# --- Optimize Itinerary ---

class ActivityPayload(BaseModel):
    place_name: str
    notes: str = ""
    start_time: str = ""
    end_time: str = ""


class DayPayload(BaseModel):
    day_number: int
    activities: List[ActivityPayload] = Field(default_factory=list)


class ItineraryPayload(BaseModel):
    name: str = "Nepal Adventure"
    days: List[DayPayload] = Field(default_factory=list)


class OptimizeRequest(BaseModel):
    itinerary: ItineraryPayload


# --- Map ---

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
