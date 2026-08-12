from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    SignupRequest, LoginRequest, AuthResponse,
    ChangePasswordRequest, ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, MessageResponse,
)
from app.services import db
from app.services.auth import (
    hash_password, verify_password, create_access_token,
    generate_reset_token, hash_reset_token, get_current_student_id,
)

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


@router.post("/change-password", response_model=MessageResponse)
def change_password(payload: ChangePasswordRequest, student_id: str = Depends(get_current_student_id)):
    student = db.get_student_auth_by_id(student_id)
    if not student or not student["password_hash"] or not verify_password(payload.current_password, student["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    db.update_password_hash(student_id, hash_password(payload.new_password))
    return MessageResponse(detail="Password changed successfully.")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest):
    student = db.get_student_auth_by_email(payload.email)
    if not student:
        # Same response whether or not the email exists, so this endpoint
        # can't be used to discover which emails have accounts.
        return ForgotPasswordResponse(detail="If that email is registered, a reset token has been issued.")

    raw_token, token_hash, expires_at = generate_reset_token()
    db.create_password_reset(str(student["student_id"]), token_hash, expires_at)

    return ForgotPasswordResponse(
        detail="If that email is registered, a reset token has been issued.",
        reset_token=raw_token,
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest):
    token_hash = hash_reset_token(payload.token)
    reset = db.get_valid_password_reset(token_hash)
    if not reset:
        raise HTTPException(status_code=400, detail="Reset token is invalid or has expired")

    db.update_password_hash(str(reset["student_id"]), hash_password(payload.new_password))
    db.mark_password_reset_used(reset["reset_id"])
    return MessageResponse(detail="Password has been reset. You can now log in with your new password.")
