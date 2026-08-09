from fastapi import APIRouter

from app.services import db

router = APIRouter()


@router.get("")
def list_careers():
    return db.get_all_careers()
