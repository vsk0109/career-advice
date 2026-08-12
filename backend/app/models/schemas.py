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


# ---------- Score ----------

class CareerMatch(BaseModel):
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
