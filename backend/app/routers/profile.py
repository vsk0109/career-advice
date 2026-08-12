from fastapi import APIRouter, HTTPException

from app.models.schemas import ProfileIntake, ProfileResponse
from app.services import db
from app.services.scoring_engine import compute_riasec_scores
from app.data.riasec_questions import QUESTION_DIMENSIONS

router = APIRouter()


@router.post("", response_model=ProfileResponse)
def create_profile(payload: ProfileIntake):
    riasec_scores = compute_riasec_scores(payload.riasec_answers, QUESTION_DIMENSIONS)

    profile_data = {
        "name": payload.name,
        "email": payload.email,
        "interests": payload.interests,
        "hobbies": payload.hobbies,
        "academics": payload.academics,
        "self_rated_skills": payload.self_rated_skills,
        "riasec_scores": riasec_scores,
    }
    student_id = db.save_profile(profile_data)

    return ProfileResponse(student_id=student_id, **profile_data)


@router.get("/{student_id}", response_model=ProfileResponse)
def get_profile(student_id: str):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(student_id=student_id, **profile)
