from sqlalchemy.orm import Session
from app.repositories.theory import theory_repo
from app.models.theory import TheoryArticle
from app.schemas.theory import TheoryArticleCreate

def create_theory_article(db: Session, theory_in: TheoryArticleCreate, teacher_id: int) -> TheoryArticle:
    return theory_repo.create_with_teacher(db, obj_in=theory_in, teacher_id=teacher_id)
