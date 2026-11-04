import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.permissions import visible_content
from app.models.theory import TheoryArticle, TheoryAttachment
from app.models.user import User
from app.repositories.theory import theory_repo
from app.schemas.theory import TheoryArticleCreate, TheoryArticleUpdate, TheoryLinkCreate

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_ARTICLE = 20
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/avif"}

# Files are written before the row exists and removed only after the row is gone,
# so the disk never misses a file that the database still references.
_DELETE_ON_COMMIT = "theory_delete_on_commit"
_DELETE_ON_ROLLBACK = "theory_delete_on_rollback"


def upload_dir() -> Path:
    return Path(settings.UPLOAD_DIR)


def _unlink(session: Session, key: str):
    for name in session.info.pop(key, []):
        (upload_dir() / name).unlink(missing_ok=True)


@event.listens_for(Session, "after_commit")
def _cleanup_after_commit(session):
    session.info.pop(_DELETE_ON_ROLLBACK, None)
    _unlink(session, _DELETE_ON_COMMIT)


@event.listens_for(Session, "after_soft_rollback")
def _cleanup_after_rollback(session, previous_transaction):
    if not session.in_transaction():
        session.info.pop(_DELETE_ON_COMMIT, None)
        _unlink(session, _DELETE_ON_ROLLBACK)


def detect_mime(head: bytes, path: Path) -> str | None:
    """Identify an allowed file type from its content, never from the client's claim."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[4:8] == b"ftyp" and head[8:12] in (b"avif", b"avis"):
        return "image/avif"
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as archive:
                if "word/document.xml" in archive.namelist():
                    return DOCX_MIME
        except zipfile.BadZipFile:
            return None
    return None


def _owned_article(db: Session, article_id: int, teacher_id: int, *, lock: bool = False) -> TheoryArticle:
    query = db.query(TheoryArticle).filter(TheoryArticle.id == article_id)
    if lock:
        query = query.with_for_update()
    article = query.first()
    if article is None or article.teacher_id != teacher_id:
        raise HTTPException(404, "Theory article not found")
    return article


def create_theory_article(db: Session, theory_in: TheoryArticleCreate, teacher_id: int) -> TheoryArticle:
    return theory_repo.create_with_teacher(db, obj_in=theory_in, teacher_id=teacher_id)


def update_theory_article(db: Session, article_id: int, theory_in: TheoryArticleUpdate, teacher_id: int) -> TheoryArticle:
    article = _owned_article(db, article_id, teacher_id)
    return theory_repo.update(db, db_obj=article, obj_in=theory_in)


def delete_theory_article(db: Session, article_id: int, teacher_id: int) -> None:
    article = _owned_article(db, article_id, teacher_id)
    stored = [a.stored_name for a in article.attachments if a.stored_name]
    db.delete(article)
    db.flush()
    db.info.setdefault(_DELETE_ON_COMMIT, []).extend(stored)


def _next_position(db: Session, article: TheoryArticle) -> int:
    count = db.query(TheoryAttachment).filter(TheoryAttachment.article_id == article.id).count()
    if count >= MAX_ATTACHMENTS_PER_ARTICLE:
        raise HTTPException(409, f"A post can have at most {MAX_ATTACHMENTS_PER_ARTICLE} attachments")
    return count


def add_file_attachment(db: Session, article_id: int, teacher_id: int, file: UploadFile) -> TheoryAttachment:
    # Lock the article so concurrent uploads cannot exceed the attachment limit.
    article = _owned_article(db, article_id, teacher_id, lock=True)
    position = _next_position(db, article)
    directory = upload_dir()
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = uuid4().hex
    path = directory / stored_name
    size = 0
    head = b""
    try:
        with path.open("xb") as buffer:
            while chunk := file.file.read(64 * 1024):
                size += len(chunk)
                if size > MAX_ATTACHMENT_BYTES:
                    raise HTTPException(413, "File must not exceed 10 MB")
                if len(head) < 32:
                    head += chunk[: 32 - len(head)]
                buffer.write(chunk)
        if size == 0:
            raise HTTPException(422, "File is empty")
        mime = detect_mime(head, path)
        if mime is None:
            raise HTTPException(415, "Only PNG, JPEG, GIF, WebP, AVIF, PDF and DOCX files are allowed")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    db.info.setdefault(_DELETE_ON_ROLLBACK, []).append(stored_name)
    original = Path(file.filename or "").name[:255] or stored_name
    attachment = TheoryAttachment(article_id=article.id, kind="image" if mime in IMAGE_TYPES else "file",
                                  stored_name=stored_name, original_name=original, mime_type=mime,
                                  size_bytes=size, position=position)
    db.add(attachment)
    db.flush()
    return attachment


def add_link_attachment(db: Session, article_id: int, teacher_id: int, link: TheoryLinkCreate) -> TheoryAttachment:
    article = _owned_article(db, article_id, teacher_id, lock=True)
    url = str(link.url)
    attachment = TheoryAttachment(article_id=article.id, kind="link", url=url,
                                  original_name=link.title.strip() or url[:255],
                                  position=_next_position(db, article))
    db.add(attachment)
    db.flush()
    return attachment


def delete_attachment(db: Session, article_id: int, attachment_id: int, teacher_id: int) -> None:
    _owned_article(db, article_id, teacher_id)
    attachment = db.query(TheoryAttachment).filter(TheoryAttachment.id == attachment_id,
                                                   TheoryAttachment.article_id == article_id).first()
    if attachment is None:
        raise HTTPException(404, "Attachment not found")
    stored = attachment.stored_name
    db.delete(attachment)
    db.flush()
    if stored:
        db.info.setdefault(_DELETE_ON_COMMIT, []).append(stored)


def readable_attachment(db: Session, attachment_id: int, user: User) -> tuple[TheoryAttachment, Path]:
    """Return a stored file the user may read, using the same rule as the article list."""
    query = visible_content(db, TheoryArticle, user).join(TheoryAttachment).filter(
        TheoryAttachment.id == attachment_id, TheoryAttachment.stored_name.isnot(None))
    if user.role != "Teacher":
        query = query.filter(TheoryArticle.is_published.is_(True))
    if query.first() is None:
        raise HTTPException(404, "Attachment not found")
    attachment = db.get(TheoryAttachment, attachment_id)
    path = upload_dir() / attachment.stored_name
    if not path.is_file():
        raise HTTPException(404, "Attachment not found")
    return attachment, path

