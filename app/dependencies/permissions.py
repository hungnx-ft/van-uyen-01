from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.class_ import Class
from app.models.user import User


def owned_class(db: Session, class_id: int, teacher_id: int, *, lock: bool = False,
                require_active: bool = False) -> Class:
    query = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id)
    if lock:
        query = query.with_for_update().populate_existing()
    classroom = query.first()
    if classroom is None:
        raise HTTPException(404, "Class not found")
    if require_active and classroom.is_archived:
        raise HTTPException(409, "Class is archived; restore it before adding students")
    return classroom


def managed_student(db: Session, student_id: int, teacher_id: int) -> User:
    # Unassigned/self-registered students are visible to teachers until they
    # are moved into a class. Once assigned, normal teacher ownership applies.
    student = db.query(User).outerjoin(Class, User.class_id == Class.id).filter(
        User.id == student_id,
        User.role == "Student",
        or_(Class.teacher_id == teacher_id, User.class_id.is_(None)),
    ).first()
    if student is None:
        raise HTTPException(404, "Student not found")
    return student


def visible_content(db: Session, model, user: User):
    """Teachers see their library; class students see their teacher's; free students see all."""
    query = db.query(model)
    if user.role == "Teacher":
        query = query.filter(model.teacher_id == user.id)
    elif user.class_id:
        query = query.filter(model.teacher_id == user.student_class.teacher_id)
    return query
