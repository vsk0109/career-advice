from pydantic import BaseModel, Field
from typing import Optional


# ---------- Auth ----------

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    student_id: str
    name: str
    email: str
    access_token: str
    token_type: str = "bearer"
    is_admin: bool = False


class MeResponse(BaseModel):
    student_id: str
    name: str
    email: str
    is_admin: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    detail: str
    # No email sending is wired up yet, so the raw reset token is returned
    # directly here rather than emailed — see docs/05_IMPLEMENTATION.md's
    # known gaps. None if the email doesn't match an account (avoids leaking
    # which emails are registered).
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    detail: str


# ---------- Profile ----------

class ProfileIntake(BaseModel):
    interests: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)
    riasec_answers: list[int] = Field(
        default_factory=list,
        description="Raw 1-5 ratings for each RIASEC quiz statement, in fixed question order.",
    )
    academics: dict[str, float] = Field(
        default_factory=dict,
        description='Subject -> mark, e.g. {"Math": 85, "Physics": 78}',
    )
    self_rated_skills: dict[str, int] = Field(
        default_factory=dict,
        description='Skill -> 1-5 self rating, e.g. {"coding": 4}',
    )


class ProfileResponse(BaseModel):
    student_id: str
    name: str
    email: str
    riasec_answers: list[int] = Field(default_factory=list)
    riasec_scores: dict[str, float]
    interests: list[str]
    hobbies: list[str]
    academics: dict[str, float]
    self_rated_skills: dict[str, int]


# ---------- Careers ----------

class CourseInfo(BaseModel):
    name: str
    level: Optional[str] = None


class CollegeInfo(BaseModel):
    name: str
    location: Optional[str] = None


class ScholarshipInfo(BaseModel):
    name: str
    eligibility: Optional[str] = None
    link: Optional[str] = None
    typical_deadline: Optional[str] = None


class CertificationInfo(BaseModel):
    name: str
    provider: Optional[str] = None


class Career(BaseModel):
    id: str
    name: str
    description: str
    riasec_tags: dict[str, float]
    relevant_subjects: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    interest_tags: list[str] = Field(default_factory=list)
    courses: list[CourseInfo] = Field(default_factory=list)
    colleges: list[CollegeInfo] = Field(default_factory=list)
    scholarships: list[ScholarshipInfo] = Field(default_factory=list)
    certifications: list[CertificationInfo] = Field(default_factory=list)
    emerging: bool = False


class CollegeDirectoryEntry(BaseModel):
    id: str
    name: str
    location: str
    state: str
    type: str
    established: Optional[int] = None
    website: Optional[str] = None
    known_for: list[str] = Field(default_factory=list)


# ---------- Score ----------

class CareerMatch(BaseModel):
    career_id: str
    career: str
    score: float
    riasec_match: float
    academic_fit: float
    interest_overlap: float
    skill_score: float
    skill_gaps: list[str]
    courses: list[CourseInfo]
    colleges: list[CollegeInfo]
    scholarships: list[ScholarshipInfo]
    certifications: list[CertificationInfo]


class ScoreResponse(BaseModel):
    top_matches: list[CareerMatch]


class InsightsRequest(BaseModel):
    top_matches: list[CareerMatch]


class InsightsResponse(BaseModel):
    explanations: dict[str, str]
    roadmap: list[str]
    emerging_trend: str


# ---------- Mentor Chat ----------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class ChatMessage(BaseModel):
    sender: str
    message: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]


# ---------- Roadmap ----------

class RoadmapStep(BaseModel):
    step_id: int
    career: str
    step_number: int
    description: str
    completed: bool


class RoadmapResponse(BaseModel):
    steps: list[RoadmapStep]


class RoadmapStepUpdate(BaseModel):
    completed: bool


# ---- Career prep (resume bullets + interview questions) ----

class PrepRequest(BaseModel):
    career_id: str
    force_refresh: bool = False


class PrepResponse(BaseModel):
    resume_bullets: list[str]
    interview_questions: list[str]
