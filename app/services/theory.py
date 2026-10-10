from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.theory import theory_repo
from app.models.theory import TheoryArticle
from app.schemas.theory import TheoryArticleCreate, TheoryArticleUpdate

def create_theory_article(db: Session, theory_in: TheoryArticleCreate, teacher_id: int) -> TheoryArticle:
    return theory_repo.create_with_teacher(db, obj_in=theory_in, teacher_id=teacher_id)


def update_theory_article(db: Session, article_id: int, theory_in: TheoryArticleUpdate, teacher_id: int) -> TheoryArticle:
    article = db.get(TheoryArticle, article_id)
    if article is None or article.teacher_id != teacher_id:
        raise HTTPException(404, "Theory article not found")
    return theory_repo.update(db, db_obj=article, obj_in=theory_in)


def delete_theory_article(db: Session, article_id: int, teacher_id: int) -> None:
    article = db.get(TheoryArticle, article_id)
    if article is None or article.teacher_id != teacher_id:
        raise HTTPException(404, "Theory article not found")
    db.delete(article)
    db.flush()
