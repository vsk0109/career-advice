from fastapi import APIRouter, Depends

from app.models.schemas import ProfileIntake, ProfileResponse
from app.services import db
from app.services.auth import get_current_student_id
from app.services.scoring_engine import compute_riasec_scores
from app.data.riasec_questions import QUESTION_DIMENSIONS

router = APIRouter()


@router.post("", response_model=ProfileResponse)
def submit_profile(payload: ProfileIntake, student_id: str = Depends(get_current_student_id)):
    riasec_scores = compute_riasec_scores(payload.riasec_answers, QUESTION_DIMENSIONS)

    db.update_profile(student_id, {
        "interests": payload.interests,
        "hobbies": payload.hobbies,
        "academics": payload.academics,
        "self_rated_skills": payload.self_rated_skills,
        "riasec_scores": riasec_scores,
    })

    return ProfileResponse(student_id=student_id, **db.get_profile(student_id))


@router.get("", response_model=ProfileResponse)
def get_profile(student_id: str = Depends(get_current_student_id)):
    return ProfileResponse(student_id=student_id, **db.get_profile(student_id))
