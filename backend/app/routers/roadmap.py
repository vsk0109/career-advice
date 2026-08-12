from fastapi import APIRouter, HTTPException

from app.models.schemas import RoadmapResponse, RoadmapStepUpdate, RoadmapStep
from app.services import db

router = APIRouter()


@router.get("/{student_id}", response_model=RoadmapResponse)
def get_roadmap(student_id: str):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return RoadmapResponse(steps=db.get_roadmap(student_id))


@router.patch("/{student_id}/steps/{step_id}", response_model=RoadmapStep)
def update_step(student_id: str, step_id: int, payload: RoadmapStepUpdate):
    profile = db.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    step = db.update_roadmap_step(student_id, step_id, payload.completed)
    if not step:
        raise HTTPException(status_code=404, detail="Roadmap step not found")
    return RoadmapStep(**step)
