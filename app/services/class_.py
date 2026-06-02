from sqlalchemy.orm import Session
from app.repositories.class_ import class_repo
from app.models.class_ import Class
from app.schemas.class_ import ClassCreate
from app.services.user import move_student_class

def create_class(db: Session, class_in: ClassCreate, teacher_id: int) -> Class:
    return class_repo.create_with_teacher(db, obj_in=class_in, teacher_id=teacher_id)

def assign_student(db: Session, class_id: int, student_id: int):
    return move_student_class(db, student_id, class_id)
