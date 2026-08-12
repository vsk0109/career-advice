from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services import db
from app.services.llm_client import generate_chat_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    profile = db.get_profile(payload.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.save_chat_message(payload.student_id, "student", payload.message)
    history = db.get_chat_history(payload.student_id)
    reply = generate_chat_reply(profile, payload.message, history)
    db.save_chat_message(payload.student_id, "ai", reply)

    return ChatResponse(reply=reply)


@router.get("/chat/{student_id}", response_model=ChatHistoryResponse)
def chat_history(student_id: str):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ChatHistoryResponse(messages=db.get_chat_history(student_id))
