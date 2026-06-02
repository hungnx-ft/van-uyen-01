from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.class_ import ClassCreate, ClassResponse
from app.schemas.user import UserResponse
from app.services.class_ import create_class, assign_student
from app.repositories.class_ import class_repo
from app.dependencies.auth import get_current_teacher
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ClassResponse)
def create_new_class(
    class_in: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    return create_class(db, class_in=class_in, teacher_id=current_user.id)

@router.get("/", response_model=List[ClassResponse])
def read_classes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # Could scope this to only classes managed by current_user, but we return all for now.
    return class_repo.get_multi(db, skip=skip, limit=limit)

@router.put("/{class_id}/students/{student_id}", response_model=UserResponse)
def add_student_to_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    user = assign_student(db, class_id=class_id, student_id=student_id)
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    return user
