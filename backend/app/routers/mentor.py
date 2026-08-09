from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services import db
from app.services.llm_client import generate_chat_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    profile = db.get_profile(payload.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    reply = generate_chat_reply(profile, payload.message)
    return ChatResponse(reply=reply)
