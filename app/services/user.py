import re
import unicodedata
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, hash_default_password
from app.dependencies.permissions import managed_student, owned_class
from app.models.user import User
from app.schemas.student import StudentCreate
from app.schemas.user import AccountCreate
from app.services.auth import revoke_all_sessions

# Teacher-created and teacher-reset student accounts start with this password and
# must replace it at first login. It is shorter than the 8-character rule on purpose.
DEFAULT_STUDENT_PASSWORD = "123456"
USERNAME_NAME_MAX = 40


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


def student_username_base(full_name: str) -> str:
    """Return the ASCII 'hovaten' part of hs_<hovaten>_<id>."""
    text = full_name.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]", "", text)[:USERNAME_NAME_MAX] or "hocsinh"


def create_student(db: Session, student_in: StudentCreate, teacher_id: int) -> User:
    """Create a class student with an hs_<hovaten>_<id> username and the default password."""
    owned_class(db, student_in.class_id, teacher_id, lock=True, require_active=True)
    user = User(username=f"tmp_{uuid4().hex}", password_hash=hash_default_password(DEFAULT_STUDENT_PASSWORD),
                full_name=student_in.full_name, school_name=student_in.school_name,
                role="Student", class_id=student_in.class_id, is_active=True, must_change_password=True)
    db.add(user)
    db.flush()  # The id is part of the username.
    base = f"hs_{student_username_base(student_in.full_name)}_{user.id}"
    username, suffix = base, 2
    # A self-registered account may already use this name; never reuse it.
    while db.query(User.id).filter(User.username == username, User.id != user.id).first():
        username, suffix = f"{base}_{suffix}", suffix + 1
    user.username = username
    db.flush()
    db.refresh(user)
    return user


def create_teacher(db: Session, teacher_in: AccountCreate) -> User:
    """Only the explicit bootstrap CLI calls this function."""
    return create_account(db, teacher_in, role="Teacher")


def reset_password(db: Session, student_id: int, teacher_id: int) -> User:
    """Restore the default password and force the student to replace it at next login."""
    managed_student(db, student_id, teacher_id)
    user = db.query(User).filter(User.id == student_id).with_for_update().populate_existing().one()
    # Recheck membership after acquiring the row lock.
    managed_student(db, student_id, teacher_id)
    user.password_hash = hash_default_password(DEFAULT_STUDENT_PASSWORD)
    user.must_change_password = True
    revoke_all_sessions(db, user.id)
    db.flush()
    return user


def move_student_class(db: Session, student_id: int, new_class_id: int, teacher_id: int) -> User:
    managed_student(db, student_id, teacher_id, allow_unassigned=True)
    student = db.query(User).filter(User.id == student_id).with_for_update().populate_existing().one()
    managed_student(db, student_id, teacher_id, allow_unassigned=True)
    owned_class(db, new_class_id, teacher_id, lock=True, require_active=True)
    student.class_id = new_class_id
    db.flush()
    db.expire(student, ["student_class"])
    return student
