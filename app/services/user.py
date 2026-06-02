from sqlalchemy.orm import Session
from app.repositories.user import user as user_repo
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def create_student(db: Session, student_in: UserCreate) -> User:
    student_in.password = get_password_hash(student_in.password)
    student_in.role = "Student"
    return user_repo.create(db, obj_in=student_in)

def create_teacher(db: Session, teacher_in: UserCreate) -> User:
    teacher_in.password = get_password_hash(teacher_in.password)
    teacher_in.role = "Teacher"
    return user_repo.create(db, obj_in=teacher_in)

def reset_password(db: Session, student_id: int, new_password: str) -> User:
    db_user = user_repo.get(db, id=student_id)
    if db_user:
        return user_repo.update(db, db_obj=db_user, obj_in={"password_hash": get_password_hash(new_password)})
    return None

def move_student_class(db: Session, student_id: int, new_class_id: int) -> User:
    db_user = user_repo.get(db, id=student_id)
    if db_user:
        return user_repo.update(db, db_obj=db_user, obj_in={"class_id": new_class_id})
    return None
