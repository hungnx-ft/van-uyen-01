from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.theory import TheoryArticle
from app.schemas.theory import TheoryArticleCreate, TheoryArticleUpdate

class CRUDTheoryArticle(CRUDBase[TheoryArticle, TheoryArticleCreate, TheoryArticleUpdate]):
    def create_with_teacher(self, db: Session, *, obj_in: TheoryArticleCreate, teacher_id: int) -> TheoryArticle:
        db_obj = TheoryArticle(
            title=obj_in.title,
            content_type=obj_in.content_type,
            content=obj_in.content,
            main_category=obj_in.main_category,
            sub_category=obj_in.sub_category,
            description=obj_in.description,
            icon=obj_in.icon,
            teacher_id=teacher_id
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

theory_repo = CRUDTheoryArticle(TheoryArticle)
