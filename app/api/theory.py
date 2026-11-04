from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from app.database.session import get_db
from app.schemas.theory import (TheoryArticleCreate, TheoryArticleResponse, TheoryArticleUpdate,
                                TheoryAttachmentResponse, TheoryLinkCreate)
from app.services.theory import (add_file_attachment, add_link_attachment, create_theory_article,
                                 delete_attachment, delete_theory_article, readable_attachment,
                                 update_theory_article)
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

@router.get("/", response_model=List[TheoryArticleResponse])
def read_theories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = visible_content(db, TheoryArticle, current_user).options(selectinload(TheoryArticle.attachments))
    return query.order_by(TheoryArticle.id).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()


@router.patch("/{article_id}", response_model=TheoryArticleResponse)
def edit_theory(article_id: int, request: TheoryArticleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    return update_theory_article(db, article_id, request, current_user.id)


@router.delete("/{article_id}", status_code=204)
def remove_theory(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_teacher)):
    delete_theory_article(db, article_id, current_user.id)
    return Response(status_code=204)


@router.post("/{article_id}/attachments", response_model=TheoryAttachmentResponse, status_code=201)
def upload_attachment(article_id: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_teacher)):
    return add_file_attachment(db, article_id, current_user.id, file)


@router.post("/{article_id}/links", response_model=TheoryAttachmentResponse, status_code=201)
def add_link(article_id: int, link: TheoryLinkCreate, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_teacher)):
    return add_link_attachment(db, article_id, current_user.id, link)


@router.delete("/{article_id}/attachments/{attachment_id}", status_code=204)
def remove_attachment(article_id: int, attachment_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_teacher)):
    delete_attachment(db, article_id, attachment_id, current_user.id)
    return Response(status_code=204)


@router.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    attachment, path = readable_attachment(db, attachment_id, current_user)
    # Images and PDFs open in the reader; anything else downloads.
    disposition = "inline" if attachment.kind == "image" or attachment.mime_type == "application/pdf" else "attachment"
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(attachment.original_name)}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, max-age=3600",
    }
    return FileResponse(path, media_type=attachment.mime_type, headers=headers)
