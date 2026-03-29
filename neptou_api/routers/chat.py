from fastapi import APIRouter

from neptou_api.llm import generate_answer_anthropic
from neptou_api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    max_turns = 20
    history = req.history[-max_turns:]

    response_text, followups = await generate_answer_anthropic(
        history=history,
        place=req.place_context,
        food=req.food_context,
    )

    return ChatResponse(response=response_text, follow_up_questions=followups)
