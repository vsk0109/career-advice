from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import Career, MessageResponse
from app.services import db
from app.services.auth import get_current_admin_id

router = APIRouter()


@router.get("/careers", response_model=list[Career])
def admin_list_careers(_admin_id: str = Depends(get_current_admin_id)):
    return db.get_all_careers()


@router.post("/careers", response_model=Career, status_code=201)
def admin_create_career(payload: Career, _admin_id: str = Depends(get_current_admin_id)):
    if db.get_career_by_id(payload.id):
        raise HTTPException(status_code=409, detail="A career with this id already exists")
    db.create_career(payload.model_dump())
    return db.get_career_by_id(payload.id)


@router.put("/careers/{career_id}", response_model=Career)
def admin_update_career(career_id: str, payload: Career, _admin_id: str = Depends(get_current_admin_id)):
    if not db.get_career_by_id(career_id):
        raise HTTPException(status_code=404, detail="Career not found")
    db.update_career(career_id, payload.model_dump())
    return db.get_career_by_id(career_id)


@router.delete("/careers/{career_id}", response_model=MessageResponse)
def admin_delete_career(career_id: str, _admin_id: str = Depends(get_current_admin_id)):
    if not db.get_career_by_id(career_id):
        raise HTTPException(status_code=404, detail="Career not found")
    db.delete_career(career_id)
    return MessageResponse(detail="Career deleted.")
