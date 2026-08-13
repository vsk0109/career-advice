from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profile, careers, score, mentor, roadmap, auth, admin, bookmarks, prep, colleges
from app.services.db import init_db

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

@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(careers.router, prefix="/careers", tags=["careers"])
app.include_router(score.router, prefix="/score", tags=["score"])
app.include_router(mentor.router, prefix="/mentor", tags=["mentor"])
app.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
app.include_router(prep.router, prefix="/prep", tags=["prep"])
app.include_router(colleges.router, prefix="/colleges", tags=["colleges"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Career Mentor API is running. See /docs for API reference."}


@app.get("/health")
def health():
    return {"status": "healthy"}
