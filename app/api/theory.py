from pathlib import Path
from uuid import uuid4
from app.core.config import settings
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.theory import TheoryArticleCreate, TheoryArticleResponse, TheoryArticleUpdate
from app.services.theory import create_theory_article, delete_theory_article, update_theory_article
from app.repositories.theory import theory_repo
from app.dependencies.auth import get_current_teacher, get_current_user
from app.models.user import User
from app.models.theory import TheoryArticle
from app.dependencies.permissions import visible_content

router = APIRouter()


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
        
    # Do not trust a client-supplied filename as a filesystem path.
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / str(uuid4())
    size = 0
    try:
        with file_path.open("xb") as buffer:
            while chunk := file.file.read(64 * 1024):
                size += len(chunk)
                if size > 5 * 1024 * 1024:
                    raise HTTPException(422, "File must not exceed 5 MB")
                buffer.write(chunk)
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    theory_in = TheoryArticleCreate(
        title=title,
        content_type=content_type,
        content=str(file_path)
    )
    return create_theory_article(db, theory_in=theory_in, teacher_id=current_user.id)

@router.get("/", response_model=List[TheoryArticleResponse])
def read_theories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return visible_content(db, TheoryArticle, current_user).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()


@router.patch("/{article_id}", response_model=TheoryArticleResponse)
def edit_theory(article_id: int, request: TheoryArticleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return update_theory_article(db, article_id, request, current_user.id)


@router.delete("/{article_id}", status_code=204)
def remove_theory(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    delete_theory_article(db, article_id, current_user.id)
    return Response(status_code=204)
