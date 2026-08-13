from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import Career, MessageResponse
from app.services import db
from app.services.auth import get_current_student_id

router = APIRouter()


@router.get("", response_model=list[Career])
def list_bookmarks(student_id: str = Depends(get_current_student_id)):
    return db.get_bookmarked_careers(student_id)


@router.post("/{career_id}", response_model=MessageResponse)
def bookmark_career(career_id: str, student_id: str = Depends(get_current_student_id)):
    if not db.get_career_by_id(career_id):
        raise HTTPException(status_code=404, detail="Career not found")
    db.add_bookmark(student_id, career_id)
    return MessageResponse(detail="Career bookmarked.")


@router.delete("/{career_id}", response_model=MessageResponse)
def unbookmark_career(career_id: str, student_id: str = Depends(get_current_student_id)):
    db.remove_bookmark(student_id, career_id)
    return MessageResponse(detail="Bookmark removed.")
