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
