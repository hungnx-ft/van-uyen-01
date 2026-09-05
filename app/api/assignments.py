from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_teacher, get_current_user
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentResponse
from app.services.assignment import create_assignment, list_student_assignments, list_teacher_assignments

router = APIRouter()


@router.post("/", response_model=AssignmentResponse, status_code=201)
def create_new_assignment(
    request: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    return create_assignment(db, request, current_user.id)


@router.get("/", response_model=list[AssignmentResponse])
def read_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "Teacher":
        return list_teacher_assignments(db, current_user.id)
    return list_student_assignments(db, current_user)
