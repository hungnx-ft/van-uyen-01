from sqlalchemy.orm import Session

from app.dependencies.permissions import managed_student, owned_class
from app.models.user import User
from app.repositories.student import managed_students
from app.schemas.student import StudentPage, StudentResponse, StudentUpdate
from app.services.auth import revoke_all_sessions


def list_students(db: Session, teacher_id: int, *, class_id: int | None = None, q: str = "",
                  is_active: bool | None = None, include_archived: bool = False,
                  skip: int = 0, limit: int = 50) -> StudentPage:
    if class_id is not None:
        owned_class(db, class_id, teacher_id)
    query = managed_students(db, teacher_id, class_id=class_id, q=q,
                             is_active=is_active, include_archived=include_archived)
    total = query.order_by(None).count()
    return StudentPage(items=[StudentResponse.model_validate(u) for u in query.offset(skip).limit(limit).all()],
                       total=total, skip=skip, limit=limit)


def lock_student(db: Session, student_id: int, teacher_id: int) -> User:
    managed_student(db, student_id, teacher_id)
    student = db.query(User).filter(User.id == student_id).with_for_update().populate_existing().one()
    managed_student(db, student_id, teacher_id)
    return student


def update_student(db: Session, student_id: int, teacher_id: int, request: StudentUpdate) -> User:
    student = lock_student(db, student_id, teacher_id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    db.flush()
    return student


def change_student_status(db: Session, student_id: int, teacher_id: int, active: bool) -> User:
    student = lock_student(db, student_id, teacher_id)
    student.is_active = active
    if not active:
        revoke_all_sessions(db, student.id)
    db.flush()
    return student


def delete_student(db: Session, student_id: int, teacher_id: int) -> None:
    student = lock_student(db, student_id, teacher_id)
    revoke_all_sessions(db, student.id)
    db.delete(student)
    db.flush()
