from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.exam import PracticeExamCreate, PracticeExamResponse, MockExamCreate, MockExamResponse
from app.services.exam import create_practice_exam, create_mock_exam
from app.repositories.exam import practice_exam_repo, mock_exam_repo
from app.dependencies.auth import get_current_teacher, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/practice", response_model=PracticeExamResponse)
def create_new_practice_exam(
    exam_in: PracticeExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        return create_practice_exam(db, exam_in=exam_in, teacher_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/practice", response_model=List[PracticeExamResponse])
def read_practice_exams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return practice_exam_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/mock", response_model=MockExamResponse)
def create_new_mock_exam(
    exam_in: MockExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        return create_mock_exam(db, exam_in=exam_in, teacher_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/mock", response_model=List[MockExamResponse])
def read_mock_exams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return mock_exam_repo.get_multi(db, skip=skip, limit=limit)
