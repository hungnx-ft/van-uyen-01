from sqlalchemy.orm import Session

from app.models.class_ import Class
from app.repositories.base import CRUDBase
from app.schemas.class_ import ClassCreate, ClassUpdate
from app.utils.query import search_pattern


class CRUDClass(CRUDBase[Class, ClassCreate, ClassUpdate]):
    def create_with_teacher(self, db: Session, *, obj_in: ClassCreate, teacher_id: int) -> Class:
        classroom = Class(name=obj_in.name, year=obj_in.year, teacher_id=teacher_id)
        db.add(classroom)
        db.flush()
        db.refresh(classroom)
        return classroom

    def for_teacher(self, db: Session, teacher_id: int, *, q: str = "", year: str | None = None,
                    include_archived: bool = False):
        query = db.query(Class).filter(Class.teacher_id == teacher_id)
        if not include_archived:
            query = query.filter(Class.is_archived.is_(False))
        if year is not None:
            query = query.filter(Class.year == year)
        if q.strip():
            query = query.filter(Class.name.ilike(search_pattern(q.strip()), escape="\\"))
        return query.order_by(Class.id)


class_repo = CRUDClass(Class)
