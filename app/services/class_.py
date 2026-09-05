from sqlalchemy.orm import Session

from app.core.security import utcnow
from app.dependencies.permissions import owned_class
from app.models.class_ import Class
from app.models.user import User
from app.repositories.class_ import class_repo
from app.schemas.class_ import ClassCreate, ClassDetail, ClassUpdate
from app.services.user import move_student_class


def create_class(db: Session, class_in: ClassCreate, teacher_id: int) -> Class:
    return class_repo.create_with_teacher(db, obj_in=class_in, teacher_id=teacher_id)


def class_detail(db: Session, class_id: int, teacher_id: int) -> ClassDetail:
    classroom = owned_class(db, class_id, teacher_id)
    count = db.query(User).filter(User.class_id == class_id, User.role == "Student").count()
    return ClassDetail(**ClassDetail.model_validate({
        **{key: getattr(classroom, key) for key in ("id", "name", "year", "teacher_id", "is_archived", "archived_at", "created_at")},
        "student_count": count,
    }).model_dump())


def update_class(db: Session, class_id: int, teacher_id: int, request: ClassUpdate) -> Class:
    classroom = owned_class(db, class_id, teacher_id, lock=True)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(classroom, key, value)
    db.flush()
    return classroom


def archive_class(db: Session, class_id: int, teacher_id: int, archived: bool) -> Class:
    classroom = owned_class(db, class_id, teacher_id, lock=True)
    if classroom.is_archived != archived:
        classroom.is_archived = archived
        classroom.archived_at = utcnow() if archived else None
        db.flush()
    return classroom


def assign_student(db: Session, class_id: int, student_id: int, teacher_id: int):
    return move_student_class(db, student_id, class_id, teacher_id)
