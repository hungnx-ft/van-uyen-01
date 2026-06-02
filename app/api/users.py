from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user import create_student, create_teacher, reset_password, move_student_class
from app.dependencies.auth import get_current_teacher
from app.models.user import User

router = APIRouter()

@router.post("/students", response_model=UserResponse)
def create_new_student(
    student_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    return create_student(db, student_in=student_in)

@router.post("/teachers", response_model=UserResponse)
def create_new_teacher(
    teacher_in: UserCreate,
    db: Session = Depends(get_db),
    # Note: In a real app, only an Admin could create a teacher. We allow it here for simplicity.
):
    return create_teacher(db, teacher_in=teacher_in)

@router.put("/students/{student_id}/password", response_model=UserResponse)
def reset_student_password(
    student_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    if not user_in.password:
        raise HTTPException(status_code=400, detail="Password is required")
    user = reset_password(db, student_id=student_id, new_password=user_in.password)
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    return user
