from fastapi import APIRouter
from app.api import assignments, auth, users, classes, theory, exams, submissions, anti_cheat, ai

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(theory.router, prefix="/theory", tags=["theory"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(anti_cheat.router, prefix="/anti-cheat", tags=["anti-cheat"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
