from fastapi import APIRouter

from app.models.schemas import CollegeDirectoryEntry
from app.services import db

router = APIRouter()


@router.get("", response_model=list[CollegeDirectoryEntry])
def list_colleges():
    return db.get_all_colleges()
