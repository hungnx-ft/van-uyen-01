from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.class_ import Class
from app.models.user import User
from app.utils.query import search_pattern


def managed_students(db: Session, teacher_id: int, *, class_id: int | None = None,
                     q: str = "", is_active: bool | None = None, include_archived: bool = False):
    query = db.query(User).join(Class, User.class_id == Class.id).options(joinedload(User.student_class)).filter(
        User.role == "Student", Class.teacher_id == teacher_id)
    if class_id is not None:
        query = query.filter(User.class_id == class_id)
    if not include_archived:
        query = query.filter(Class.is_archived.is_(False))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    if q.strip():
        pattern = search_pattern(q.strip())
        query = query.filter(or_(User.full_name.ilike(pattern, escape="\\"),
                                 User.username.ilike(pattern, escape="\\")))
    return query.order_by(User.id)
