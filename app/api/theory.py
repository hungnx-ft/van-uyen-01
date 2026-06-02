import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.theory import TheoryArticleCreate, TheoryArticleResponse
from app.services.theory import create_theory_article
from app.repositories.theory import theory_repo
from app.dependencies.auth import get_current_teacher, get_current_user
from app.models.user import User

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=TheoryArticleResponse)
def create_new_theory(
    theory_in: TheoryArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    return create_theory_article(db, theory_in=theory_in, teacher_id=current_user.id)

@router.post("/upload", response_model=TheoryArticleResponse)
def upload_theory_file(
    title: str = Form(...),
    content_type: str = Form(...), # PDF or Image
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    if content_type not in ["PDF", "Image"]:
        raise HTTPException(status_code=400, detail="Invalid content type for upload")
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    theory_in = TheoryArticleCreate(
        title=title,
        content_type=content_type,
        content=file_path
    )
    return create_theory_article(db, theory_in=theory_in, teacher_id=current_user.id)

@router.get("/", response_model=List[TheoryArticleResponse])
def read_theories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return theory_repo.get_multi(db, skip=skip, limit=limit)
