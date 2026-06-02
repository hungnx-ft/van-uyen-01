from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.class_ import Class
from app.schemas.class_ import ClassCreate, ClassUpdate

class CRUDClass(CRUDBase[Class, ClassCreate, ClassUpdate]):
    def create_with_teacher(self, db: Session, *, obj_in: ClassCreate, teacher_id: int) -> Class:
        db_obj = Class(name=obj_in.name, teacher_id=teacher_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

class_repo = CRUDClass(Class)
