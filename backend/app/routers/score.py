from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ScoreResponse, InsightsRequest, InsightsResponse
from app.services import db
from app.services.auth import get_current_student_id
from app.services.scoring_engine import rank_careers
from app.services.llm_client import generate_career_insights

router = APIRouter()


@router.post("", response_model=ScoreResponse)
def score_profile(student_id: str = Depends(get_current_student_id)):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    careers = db.get_all_careers()
    top_matches = rank_careers(profile, careers, top_n=5)

    return ScoreResponse(top_matches=top_matches)


@router.post("/insights", response_model=InsightsResponse)
def score_insights(payload: InsightsRequest, student_id: str = Depends(get_current_student_id)):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    top_matches = [m.model_dump() for m in payload.top_matches]
    insights = generate_career_insights(profile, top_matches)

    if top_matches:
        db.save_roadmap(student_id, top_matches[0]["career"], insights["roadmap"])

    return InsightsResponse(**insights)
