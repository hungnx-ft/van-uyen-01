from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import install_error_handlers
from app.database.session import get_db
from app.core.rate_limit import ai_rate_limit

# Schema changes run through Alembic, never as an import side effect.
app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")
app.middleware("http")(ai_rate_limit)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["X-Total-Count", "Content-Disposition"])
install_error_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Welcome to VAN UYEN Backend"}


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Database is temporarily unavailable")
    return {"status": "ok", "database": "ok"}
