from fastapi import APIRouter, HTTPException

from app.models.schemas import SignupRequest, LoginRequest, AuthResponse
from app.services import db
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest):
    if db.get_student_auth_by_email(payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    student_id = db.create_account(payload.name, payload.email, hash_password(payload.password))
    token = create_access_token(student_id)
    return AuthResponse(student_id=student_id, name=payload.name, email=payload.email, access_token=token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    student = db.get_student_auth_by_email(payload.email)
    if not student or not student["password_hash"] or not verify_password(payload.password, student["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    student_id = str(student["student_id"])
    token = create_access_token(student_id)
    return AuthResponse(student_id=student_id, name=student["name"], email=student["email"], access_token=token)
