from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import RoadmapResponse, RoadmapStepUpdate, RoadmapStep
from app.services import db
from app.services.auth import get_current_student_id

router = APIRouter()


@router.get("", response_model=RoadmapResponse)
def get_roadmap(student_id: str = Depends(get_current_student_id)):
    return RoadmapResponse(steps=db.get_roadmap(student_id))


@router.patch("/steps/{step_id}", response_model=RoadmapStep)
def update_step(step_id: int, payload: RoadmapStepUpdate, student_id: str = Depends(get_current_student_id)):
    step = db.update_roadmap_step(student_id, step_id, payload.completed)
    if not step:
        raise HTTPException(status_code=404, detail="Roadmap step not found")
    return RoadmapStep(**step)
