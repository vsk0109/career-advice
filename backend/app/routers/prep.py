from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import PrepRequest, PrepResponse
from app.services import db
from app.services.auth import get_current_student_id
from app.services.llm_client import generate_career_prep

router = APIRouter()


@router.post("", response_model=PrepResponse)
def get_career_prep(payload: PrepRequest, student_id: str = Depends(get_current_student_id)):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    career = db.get_career_by_id(payload.career_id)
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    if not payload.force_refresh:
        cached = db.get_career_prep(student_id, payload.career_id)
        if cached:
            return PrepResponse(**cached)

    prep = generate_career_prep(profile, career)
    db.save_career_prep(student_id, payload.career_id, prep["resume_bullets"], prep["interview_questions"])
    return PrepResponse(**prep)
