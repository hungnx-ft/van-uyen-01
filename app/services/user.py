import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.dependencies.permissions import managed_student, owned_class
from app.models.user import User
from app.schemas.user import AccountCreate, UserCreate
from app.services.auth import revoke_all_sessions


def create_account(db: Session, account: AccountCreate, *, role: str, class_id: int | None = None) -> User:
    if db.query(User.id).filter(User.username == account.username).first():
        raise HTTPException(409, "Username already exists")
    user = User(username=account.username, password_hash=get_password_hash(account.password),
                full_name=account.full_name, school_name=account.school_name,
                role=role, class_id=class_id, is_active=True)
    db.add(user)
    db.flush()  # A concurrent duplicate is handled by the global IntegrityError handler.
    db.refresh(user)
    return user


def create_student(db: Session, student_in: UserCreate, teacher_id: int) -> User:
    owned_class(db, student_in.class_id, teacher_id, lock=True, require_active=True)
    return create_account(db, student_in, role="Student", class_id=student_in.class_id)


def create_teacher(db: Session, teacher_in: AccountCreate) -> User:
    """Only the explicit bootstrap CLI calls this function."""
    return create_account(db, teacher_in, role="Teacher")


def reset_password(db: Session, student_id: int, new_password: str, teacher_id: int) -> User:
    managed_student(db, student_id, teacher_id)
    user = db.query(User).filter(User.id == student_id).with_for_update().populate_existing().one()
    # Recheck membership after acquiring the row lock.
    managed_student(db, student_id, teacher_id)
    user.password_hash = get_password_hash(new_password)
    revoke_all_sessions(db, user.id)
    db.flush()
    return user


def move_student_class(db: Session, student_id: int, new_class_id: int, teacher_id: int) -> User:
    managed_student(db, student_id, teacher_id)
    student = db.query(User).filter(User.id == student_id).with_for_update().populate_existing().one()
    managed_student(db, student_id, teacher_id)
    owned_class(db, new_class_id, teacher_id, lock=True, require_active=True)
    student.class_id = new_class_id
    db.flush()
    db.expire(student, ["student_class"])
    return student


def create_student_credentials(db: Session, request, teacher_id: int):
    password = request.password or secrets.token_urlsafe(12)
    account = UserCreate(**{**request.model_dump(), "password": password})
    student = create_student(db, account, teacher_id)
    return student, password


def reset_student_credentials(db: Session, student_id: int, teacher_id: int):
    password = secrets.token_urlsafe(12)
    return reset_password(db, student_id, password, teacher_id), password
