from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profile, careers, score, mentor

app = FastAPI(
    title="AI-Powered Career Mentor API",
    description="Backend for the AI-Powered Career Mentor app",
    version="0.1.0",
)

# CORS — allow the frontend dev server and deployed frontend URL.
# Add your deployed Vercel URL here once you have it.
origins = [
    "http://localhost:5173",  # Vite dev server default
    "http://localhost:3000",
    # "https://your-app.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(careers.router, prefix="/careers", tags=["careers"])
app.include_router(score.router, prefix="/score", tags=["score"])
app.include_router(mentor.router, prefix="/mentor", tags=["mentor"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Career Mentor API is running. See /docs for API reference."}


@app.get("/health")
def health():
    return {"status": "healthy"}
